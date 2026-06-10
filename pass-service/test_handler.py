"""
Local unit tests for handler.py — no AWS needed (boto3 fully stubbed).
Run: python3 test_handler.py
"""

import json
import os
import sys
import types
from datetime import datetime, timezone

# ---------------------------------------------------------------- boto3 stub


class ConditionalCheckFailedException(Exception):
    def __init__(self):
        super().__init__("The conditional request failed")
        self.response = {"Error": {"Code": "ConditionalCheckFailedException"}}


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item, ConditionExpression=None, **kw):
        key = Item.get("endpoint") or (
            Item["deviceLibraryIdentifier"],
            Item["serialNumber"],
        )
        if ConditionExpression == "attribute_not_exists(endpoint)" and key in self.items:
            raise ConditionalCheckFailedException()
        self.items[key] = Item

    def delete_item(self, Key):
        key = Key.get("endpoint") or (
            Key["deviceLibraryIdentifier"],
            Key["serialNumber"],
        )
        self.items.pop(key, None)

    def query(self, KeyConditionExpression=None, **kw):
        return {"Items": list(self.items.values())}


class FakeBody:
    def read(self):
        return b"PKPASS_BYTES"


class FakeS3:
    def get_object(self, Bucket, Key):
        return {"Body": FakeBody(), "LastModified": datetime.now(timezone.utc)}


fake_reg_table = FakeTable()
fake_push_table = FakeTable()


class FakeResource:
    def Table(self, name):
        return fake_push_table if name == "web-push-subscriptions" else fake_reg_table


class _Key:
    def __init__(self, name):
        self.name = name

    def eq(self, value):
        return (self.name, value)


boto3_stub = types.ModuleType("boto3")
dynamodb_mod = types.ModuleType("boto3.dynamodb")
conditions_mod = types.ModuleType("boto3.dynamodb.conditions")
conditions_mod.Key = _Key
dynamodb_mod.conditions = conditions_mod
boto3_stub.dynamodb = dynamodb_mod
boto3_stub.resource = lambda name: FakeResource()
boto3_stub.client = lambda name: FakeS3()
sys.modules["boto3"] = boto3_stub
sys.modules["boto3.dynamodb"] = dynamodb_mod
sys.modules["boto3.dynamodb.conditions"] = conditions_mod

os.environ["AUTH_TOKEN"] = "test-token-123"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handler  # noqa: E402

# ------------------------------------------------------------------ helpers

GOOD_ORIGIN = "https://contact.jamestannahill.com"
FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"
GOOD_SUB = {
    "subscription": {
        "endpoint": FCM_ENDPOINT,
        "keys": {"p256dh": "BPubKeyMaterial", "auth": "authSecret"},
    }
}


def make_event(method, path, body=None, origin=None, referer=None,
               auth=None, source_ip="1.2.3.4"):
    headers = {}
    if origin:
        headers["Origin"] = origin
    if referer:
        headers["Referer"] = referer
    if auth:
        headers["Authorization"] = auth
    return {
        "requestContext": {"http": {"method": method, "sourceIp": source_ip}},
        "rawPath": path,
        "headers": headers,
        "body": json.dumps(body) if isinstance(body, dict) else (body or ""),
    }


results = []


def check(name, got, want):
    ok = got == want
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: status {got} (want {want})")


# -------------------------------------------------------------------- cases

# 1. subscribe with no Origin header → 403
r = handler.handler(make_event("POST", "/api/push/subscribe", GOOD_SUB), None)
check("subscribe no origin", r["statusCode"], 403)

# 2. subscribe with wrong origin → 403
r = handler.handler(make_event("POST", "/api/push/subscribe", GOOD_SUB,
                               origin="https://evil.example.com"), None)
check("subscribe wrong origin", r["statusCode"], 403)

# 3. subscribe with correct origin → 201
r = handler.handler(make_event("POST", "/api/push/subscribe", GOOD_SUB,
                               origin=GOOD_ORIGIN), None)
check("subscribe correct origin", r["statusCode"], 201)

# 4. subscribe via Referer fallback (no Origin) → 201
r = handler.handler(make_event("POST", "/api/push/subscribe", GOOD_SUB,
                               referer=GOOD_ORIGIN + "/contact.html",
                               source_ip="4.4.4.4"), None)
check("subscribe referer fallback", r["statusCode"], 201)

# 5. oversize body → 400
big = {"subscription": {"endpoint": FCM_ENDPOINT,
                        "keys": {"p256dh": "x", "auth": "y"},
                        "pad": "z" * 5000}}
r = handler.handler(make_event("POST", "/api/push/subscribe", big,
                               origin=GOOD_ORIGIN), None)
check("oversize body", r["statusCode"], 400)

# 6. non-push-service endpoint domain → 400
bad = {"subscription": {"endpoint": "https://attacker.example.com/hook",
                        "keys": {"p256dh": "x", "auth": "y"}}}
r = handler.handler(make_event("POST", "/api/push/subscribe", bad,
                               origin=GOOD_ORIGIN), None)
check("garbage endpoint domain", r["statusCode"], 400)

# 7. http (not https) endpoint → 400
bad = {"subscription": {"endpoint": "http://fcm.googleapis.com/fcm/send/x",
                        "keys": {"p256dh": "x", "auth": "y"}}}
r = handler.handler(make_event("POST", "/api/push/subscribe", bad,
                               origin=GOOD_ORIGIN), None)
check("http endpoint", r["statusCode"], 400)

# 8. lookalike domain (evil-googleapis.com) → 400
bad = {"subscription": {"endpoint": "https://evil-googleapis.com/send/x",
                        "keys": {"p256dh": "x", "auth": "y"}}}
r = handler.handler(make_event("POST", "/api/push/subscribe", bad,
                               origin=GOOD_ORIGIN), None)
check("lookalike domain", r["statusCode"], 400)

# 9. missing keys → 400
bad = {"subscription": {"endpoint": FCM_ENDPOINT}}
r = handler.handler(make_event("POST", "/api/push/subscribe", bad,
                               origin=GOOD_ORIGIN), None)
check("missing keys", r["statusCode"], 400)

# 10. per-IP daily cap: 5 allowed, 6th → 429
statuses = []
for i in range(6):
    sub = {"subscription": {"endpoint": f"{FCM_ENDPOINT}/n{i}",
                            "keys": {"p256dh": "x", "auth": "y"}}}
    r = handler.handler(make_event("POST", "/api/push/subscribe", sub,
                                   origin=GOOD_ORIGIN,
                                   source_ip="9.9.9.9"), None)
    statuses.append(r["statusCode"])
check("per-IP cap first five", statuses[:5], [201] * 5)
check("per-IP cap sixth", statuses[5], 429)

# 11. unsubscribe with correct origin → 200
r = handler.handler(make_event("DELETE", "/api/push/unsubscribe",
                               {"endpoint": FCM_ENDPOINT},
                               origin=GOOD_ORIGIN), None)
check("unsubscribe correct origin", r["statusCode"], 200)

# 12. unsubscribe with no origin → 403
r = handler.handler(make_event("DELETE", "/api/push/unsubscribe",
                               {"endpoint": FCM_ENDPOINT}), None)
check("unsubscribe no origin", r["statusCode"], 403)

# 13. unsubscribe cannot target ratelimit counter items → 400
r = handler.handler(make_event("DELETE", "/api/push/unsubscribe",
                               {"endpoint": "ratelimit#9.9.9.9#2026-06-10"},
                               origin=GOOD_ORIGIN), None)
check("unsubscribe counter key blocked", r["statusCode"], 400)

# 14. PassKit pass fetch with token, no Origin → 200
r = handler.handler(make_event(
    "GET", "/api/passes/v1/passes/pass.com.jamestannahill.contact/serial-1",
    auth="ApplePass test-token-123"), None)
check("passkit pass fetch with token", r["statusCode"], 200)

# 15. PassKit pass fetch wrong token → 401
r = handler.handler(make_event(
    "GET", "/api/passes/v1/passes/pass.com.jamestannahill.contact/serial-1",
    auth="ApplePass wrong"), None)
check("passkit pass fetch wrong token", r["statusCode"], 401)

# 16. PassKit device register with token, no Origin → 201
r = handler.handler(make_event(
    "POST",
    "/api/passes/v1/devices/dev1/registrations/pass.com.jamestannahill.contact/serial-1",
    {"pushToken": "tok123"}, auth="ApplePass test-token-123"), None)
check("passkit register with token", r["statusCode"], 201)

# 17. registrations list (unauthenticated by spec), no Origin → 200
r = handler.handler(make_event(
    "GET", "/api/passes/v1/devices/dev1/registrations/pass.com.jamestannahill.contact"),
    None)
check("registrations list", r["statusCode"], 200)

# 18. log endpoint, no Origin → 200
r = handler.handler(make_event("POST", "/api/passes/v1/log",
                               {"logs": ["x"]}), None)
check("log endpoint", r["statusCode"], 200)

# ------------------------------------------------------------------ summary

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
