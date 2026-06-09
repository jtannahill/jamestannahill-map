"""
Apple Wallet Pass Web Service
Endpoints per Apple spec:
  POST   /v1/devices/{deviceID}/registrations/{passTypeID}/{serial} — register
  DELETE /v1/devices/{deviceID}/registrations/{passTypeID}/{serial} — unregister
  GET    /v1/devices/{deviceID}/registrations/{passTypeID}          — get serials
  GET    /v1/passes/{passTypeID}/{serial}                          — get latest pass
  POST   /v1/log                                                   — log errors
"""

import hmac
import json
import os
import time
import boto3
import hashlib
import zipfile
import io
import base64
import subprocess
import tempfile

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ.get("TABLE_NAME", "wallet-pass-registrations")
PASS_BUCKET = os.environ.get("PASS_BUCKET", "contact.jamestannahill.com")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
PUSH_TABLE_NAME = "web-push-subscriptions"

table = dynamodb.Table(TABLE_NAME)
push_table = dynamodb.Table(PUSH_TABLE_NAME)


def handler(event, context):
    method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", ""))
    path = event.get("path", event.get("rawPath", ""))
    headers = event.get("headers", {})

    # Handle base64 encoded body from API Gateway
    raw_body = event.get("body", "") or ""
    if event.get("isBase64Encoded") and raw_body:
        import base64 as b64
        raw_body = b64.b64decode(raw_body).decode("utf-8")

    # Normalize header keys to lowercase
    headers = {k.lower(): v for k, v in headers.items()} if headers else {}

    print(f"{method} {path}")

    # CORS preflight
    if method == "OPTIONS":
        return cors_response(200, "")

    # Push subscription routes (no Apple auth required)
    if "/api/push/" in path:
        return handle_push(method, path, raw_body)

    # Requests arrive as /api/passes/v1/... behind CloudFront; strip the
    # service prefix so route checks match the v1 paths.
    route = path.split("/api/passes", 1)[-1] if "/api/passes" in path else path
    parts = route.strip("/").split("/")

    # Auth check per Apple spec: pass fetch and device register/unregister
    # require "Authorization: ApplePass <token>". The registrations-list GET
    # and the log endpoint are unauthenticated by spec.
    needs_auth = (
        (method == "GET" and "passes" in parts)
        or (method in ("POST", "DELETE") and "registrations" in parts)
    )
    if needs_auth:
        auth = headers.get("authorization", "")
        if not AUTH_TOKEN or not hmac.compare_digest(auth, f"ApplePass {AUTH_TOKEN}"):
            return response(401, "Unauthorized")

    # POST /v1/log
    if method == "POST" and route.endswith("/log"):
        body = json.loads(raw_body) if raw_body else {}
        print(f"Pass log: {json.dumps(body)}")
        return response(200, "OK")

    # POST /v1/devices/{deviceID}/registrations/{passTypeID}/{serial}
    if method == "POST" and "registrations" in parts and len(parts) >= 5:
        device_id = parts[-3] if "registrations" in parts[-4] else extract_part(parts, "devices")
        serial = parts[-1]
        body = json.loads(raw_body) if raw_body else {}
        push_token = body.get("pushToken", "")

        table.put_item(Item={
            "deviceLibraryIdentifier": device_id,
            "serialNumber": serial,
            "pushToken": push_token,
            "registeredAt": int(time.time()),
        })
        print(f"Registered device={device_id} serial={serial} token={push_token[:20]}...")
        return response(201, "Created")

    # DELETE /v1/devices/{deviceID}/registrations/{passTypeID}/{serial}
    if method == "DELETE" and "registrations" in parts:
        device_id = extract_part(parts, "devices")
        serial = parts[-1]

        table.delete_item(Key={
            "deviceLibraryIdentifier": device_id,
            "serialNumber": serial,
        })
        print(f"Unregistered device={device_id} serial={serial}")
        return response(200, "OK")

    # GET /v1/devices/{deviceID}/registrations/{passTypeID}
    if method == "GET" and "registrations" in parts and "passes" not in parts:
        device_id = extract_part(parts, "devices")

        result = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("deviceLibraryIdentifier").eq(device_id)
        )

        serials = [item["serialNumber"] for item in result.get("Items", [])]
        if not serials:
            return response(204, "")

        return response(200, json.dumps({
            "serialNumbers": serials,
            "lastUpdated": str(int(time.time()))
        }))

    # GET /v1/passes/{passTypeID}/{serial}
    if method == "GET" and "passes" in parts:
        try:
            obj = s3.get_object(Bucket=PASS_BUCKET, Key="JamesTannahill.pkpass")
            pass_data = obj["Body"].read()
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/vnd.apple.pkpass",
                    "Content-Disposition": "attachment; filename=JamesTannahill.pkpass",
                    "Last-Modified": obj["LastModified"].strftime("%a, %d %b %Y %H:%M:%S GMT"),
                },
                "body": base64.b64encode(pass_data).decode("utf-8"),
                "isBase64Encoded": True,
            }
        except Exception as e:
            print(f"Error getting pass: {e}")
            return response(500, "Error")

    return response(404, "Not found")


def handle_push(method, path, raw_body):
    if method == "POST" and path.endswith("/subscribe"):
        try:
            body = json.loads(raw_body) if raw_body else {}
            sub = body.get("subscription")
            if not sub or "endpoint" not in sub:
                return cors_response(400, {"error": "Missing subscription"})
            push_table.put_item(Item={
                "endpoint": sub["endpoint"],
                "subscription": json.dumps(sub),
                "subscribedAt": int(time.time()),
            })
            print(f"Push subscriber added: {sub['endpoint'][:60]}...")
            return cors_response(201, {"status": "subscribed"})
        except Exception as e:
            print(f"Subscribe error: {e}")
            return cors_response(500, {"error": str(e)})

    if method == "DELETE" and path.endswith("/unsubscribe"):
        try:
            body = json.loads(raw_body) if raw_body else {}
            endpoint = body.get("endpoint")
            if endpoint:
                push_table.delete_item(Key={"endpoint": endpoint})
            return cors_response(200, {"status": "unsubscribed"})
        except Exception as e:
            return cors_response(500, {"error": str(e)})

    return cors_response(404, {"error": "Not found"})


def cors_response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://contact.jamestannahill.com",
            "Access-Control-Allow-Methods": "POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": body if isinstance(body, str) else json.dumps(body),
    }


def extract_part(parts, after):
    """Extract the value after a given path segment."""
    for i, p in enumerate(parts):
        if p == after and i + 1 < len(parts):
            return parts[i + 1]
    return ""


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": body if isinstance(body, str) else json.dumps(body),
    }
