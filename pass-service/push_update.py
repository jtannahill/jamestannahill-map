"""
Push pass updates to all registered devices via APNs.
Usage: python3 push_update.py

This sends a silent push to every registered device, causing iOS to
call GET /v1/passes/{passTypeID}/{serial} and update the card.
"""

import json
import os
import time
import ssl
import http.client
import boto3

PASS_TYPE_ID = "pass.com.jamestannahill.contact"
TABLE_NAME = os.environ.get("TABLE_NAME", "wallet-pass-registrations")
CERT_PATH = os.path.expanduser("~/pass-cert.pem")
KEY_PATH = os.path.expanduser("~/pass-key.pem")

# APNs production endpoint
APNS_HOST = "api.push.apple.com"
APNS_PORT = 443


def get_all_tokens():
    """Get all registered push tokens from DynamoDB."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)
    result = table.scan()
    tokens = set()
    for item in result.get("Items", []):
        token = item.get("pushToken", "")
        if token:
            tokens.add(token)
    return tokens


def push_to_device(token, context):
    """Send empty push notification to trigger pass update."""
    payload = json.dumps({}).encode("utf-8")

    ctx = ssl.create_default_context()
    ctx.load_cert_chain(CERT_PATH, KEY_PATH)

    conn = http.client.HTTPSConnection(APNS_HOST, APNS_PORT, context=ctx)
    headers = {
        "apns-topic": PASS_TYPE_ID,
        "apns-push-type": "background",
        "apns-priority": "5",
    }

    conn.request("POST", f"/3/device/{token}", payload, headers)
    resp = conn.getresponse()
    status = resp.status
    body = resp.read().decode("utf-8")
    conn.close()

    return status, body


def main():
    tokens = get_all_tokens()
    print(f"Found {len(tokens)} registered device(s)")

    for token in tokens:
        try:
            status, body = push_to_device(token, None)
            result = "OK" if status == 200 else f"FAIL ({body})"
            print(f"  {token[:20]}... → {status} {result}")
        except Exception as e:
            print(f"  {token[:20]}... → ERROR: {e}")

    print("Done")


if __name__ == "__main__":
    main()
