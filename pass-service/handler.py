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
from urllib.parse import urlparse

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ.get("TABLE_NAME", "wallet-pass-registrations")
PASS_BUCKET = os.environ.get("PASS_BUCKET", "contact.jamestannahill.com")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
PUSH_TABLE_NAME = "web-push-subscriptions"

# Push route hardening
ALLOWED_ORIGIN = "https://contact.jamestannahill.com"
MAX_PUSH_BODY_BYTES = 4096
MAX_ENDPOINT_LENGTH = 2048
PUSH_SUBS_PER_IP_PER_DAY = 5
RATE_ITEM_TTL_SECONDS = 172800  # counter items expire 2 days out
# Hosts the browser push services actually live on. Endpoint host must
# equal one of these or be a subdomain of one.
PUSH_ENDPOINT_DOMAINS = (
    "googleapis.com",   # Chrome / FCM
    "mozilla.com",      # Firefox
    "mozaws.net",       # Firefox (legacy autopush)
    "push.apple.com",   # Safari
    "windows.com",      # Edge / WNS
)

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

    # Push subscription routes (no Apple auth required, but locked to the
    # site origin and rate limited; Wallet never calls these)
    if "/api/push/" in path:
        source_ip = (
            event.get("requestContext", {}).get("http", {}).get("sourceIp")
            or event.get("requestContext", {}).get("identity", {}).get("sourceIp")
            or "unknown"
        )
        return handle_push(method, path, raw_body, headers, source_ip)

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


def handle_push(method, path, raw_body, headers, source_ip):
    # Server-side origin enforcement: only the site itself may manage
    # subscriptions. Browsers always send Origin on cross-context POST and
    # DELETE fetches; curl/scripts must spoof it deliberately.
    if not allowed_origin(headers):
        print(f"Push request rejected: bad origin ip={source_ip}")
        return cors_response(403, {"error": "Forbidden"})

    if len(raw_body.encode("utf-8")) > MAX_PUSH_BODY_BYTES:
        return cors_response(400, {"error": "Body too large"})

    if method == "POST" and path.endswith("/subscribe"):
        try:
            body = json.loads(raw_body) if raw_body else {}
            sub = body.get("subscription")
            if not valid_subscription(sub):
                return cors_response(400, {"error": "Invalid subscription"})
            if not push_rate_limit_ok(source_ip):
                print(f"Push subscribe rate limited ip={source_ip}")
                return cors_response(429, {"error": "Too many requests"})
            push_table.put_item(Item={
                "endpoint": sub["endpoint"],
                "subscription": json.dumps(sub),
                "subscribedAt": int(time.time()),
            })
            print(f"Push subscriber added: {sub['endpoint'][:60]}...")
            return cors_response(201, {"status": "subscribed"})
        except json.JSONDecodeError:
            return cors_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            print(f"Subscribe error: {e}")
            return cors_response(500, {"error": str(e)})

    if method == "DELETE" and path.endswith("/unsubscribe"):
        try:
            body = json.loads(raw_body) if raw_body else {}
            endpoint = body.get("endpoint")
            if not valid_push_endpoint(endpoint):
                return cors_response(400, {"error": "Invalid endpoint"})
            push_table.delete_item(Key={"endpoint": endpoint})
            return cors_response(200, {"status": "unsubscribed"})
        except json.JSONDecodeError:
            return cors_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            return cors_response(500, {"error": str(e)})

    return cors_response(404, {"error": "Not found"})


def allowed_origin(headers):
    """True if the request came from the site origin (Referer fallback)."""
    origin = headers.get("origin", "")
    if origin:
        return origin == ALLOWED_ORIGIN
    referer = headers.get("referer", "")
    return referer == ALLOWED_ORIGIN or referer.startswith(ALLOWED_ORIGIN + "/")


def valid_push_endpoint(endpoint):
    """Endpoint must be an https URL on a known browser push service."""
    if not isinstance(endpoint, str) or not endpoint or len(endpoint) > MAX_ENDPOINT_LENGTH:
        return False
    try:
        parsed = urlparse(endpoint)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == d or host.endswith("." + d) for d in PUSH_ENDPOINT_DOMAINS)


def valid_subscription(sub):
    """Standard web-push subscription shape: endpoint + p256dh/auth keys."""
    if not isinstance(sub, dict):
        return False
    if not valid_push_endpoint(sub.get("endpoint")):
        return False
    keys = sub.get("keys")
    if not isinstance(keys, dict):
        return False
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")
    return (
        isinstance(p256dh, str) and 0 < len(p256dh) <= 256
        and isinstance(auth, str) and 0 < len(auth) <= 64
    )


def push_rate_limit_ok(source_ip):
    """Cap subscribe writes per source IP per UTC day.

    Conditional writes keyed on ip+date claim one of N daily slots; once
    every slot exists, further subscribes are rejected. Slot items live
    under a 'ratelimit#' key prefix that can never collide with real
    endpoints (those are https URLs) and carry an expiresAt TTL so
    DynamoDB cleans them up.
    """
    day = time.strftime("%Y-%m-%d", time.gmtime())
    expires_at = int(time.time()) + RATE_ITEM_TTL_SECONDS
    for slot in range(PUSH_SUBS_PER_IP_PER_DAY):
        try:
            push_table.put_item(
                Item={
                    "endpoint": f"ratelimit#{source_ip}#{day}#{slot}",
                    "expiresAt": expires_at,
                },
                ConditionExpression="attribute_not_exists(endpoint)",
            )
            return True
        except Exception as e:
            code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if code == "ConditionalCheckFailedException":
                continue
            raise
    return False


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
