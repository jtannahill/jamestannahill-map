"""
Apple Wallet Pass Web Service
Endpoints per Apple spec:
  POST   /v1/devices/{deviceID}/registrations/{passTypeID}/{serial} — register
  DELETE /v1/devices/{deviceID}/registrations/{passTypeID}/{serial} — unregister
  GET    /v1/devices/{deviceID}/registrations/{passTypeID}          — get serials
  GET    /v1/passes/{passTypeID}/{serial}                          — get latest pass
  POST   /v1/log                                                   — log errors
"""

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
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "vxwxd7J8AlNNFPS8k0a0FfUFtq0ewzFdc")

table = dynamodb.Table(TABLE_NAME)


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

    # Auth check (except for log endpoint and GET passes)
    if "/v1/log" not in path:
        auth = headers.get("authorization", "")
        if not path.endswith("/log") and "passes" not in path:
            if auth != f"ApplePass {AUTH_TOKEN}":
                return response(401, "Unauthorized")

    # Route
    parts = path.strip("/").split("/")

    # POST /v1/log
    if method == "POST" and path.endswith("/log"):
        body = json.loads(raw_body) if raw_body else {}
        print(f"Pass log: {json.dumps(body)}")
        return response(200, "OK")

    # POST /v1/devices/{deviceID}/registrations/{passTypeID}/{serial}
    if method == "POST" and "registrations" in path and len(parts) >= 5:
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
    if method == "DELETE" and "registrations" in path:
        device_id = extract_part(parts, "devices")
        serial = parts[-1]

        table.delete_item(Key={
            "deviceLibraryIdentifier": device_id,
            "serialNumber": serial,
        })
        print(f"Unregistered device={device_id} serial={serial}")
        return response(200, "OK")

    # GET /v1/devices/{deviceID}/registrations/{passTypeID}
    if method == "GET" and "registrations" in path and "passes" not in path:
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
    if method == "GET" and "passes" in path:
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
