#!/bin/bash
# Update and push Apple Wallet pass to all registered devices
# Usage: ./update-pass.sh
#
# Edit pass-build/pass.json first, then run this.
# It rebuilds, signs, uploads, invalidates cache, and pushes to all devices.

set -e

PASS_DIR="$HOME/pass-build/pass.pass"
PKPASS="$HOME/pass-build/JamesTannahill.pkpass"
CERT="$HOME/pass-cert.pem"
KEY="$HOME/pass-key.pem"
WWDR="$HOME/wwdr.pem"
BUCKET="contact.jamestannahill.com"
CF_DIST="E28BIZ72OMRUET"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Wallet Pass Updater ==="
echo ""

# 1. Rebuild manifest
echo "[1/5] Building manifest..."
python3 -c "
import hashlib, json, os
pass_dir = '$PASS_DIR'
manifest = {}
for f in os.listdir(pass_dir):
    if f in ('manifest.json', 'signature'): continue
    path = os.path.join(pass_dir, f)
    if os.path.isfile(path):
        with open(path, 'rb') as fh:
            manifest[f] = hashlib.sha1(fh.read()).hexdigest()
with open(os.path.join(pass_dir, 'manifest.json'), 'w') as fh:
    json.dump(manifest, fh, indent=2)
print(f'  {len(manifest)} files hashed')
"

# 2. Sign
echo "[2/5] Signing..."
openssl smime -sign \
  -signer "$CERT" \
  -inkey "$KEY" \
  -certfile "$WWDR" \
  -in "$PASS_DIR/manifest.json" \
  -out "$PASS_DIR/signature" \
  -outform DER \
  -binary 2>/dev/null
echo "  Signed"

# 3. Package
echo "[3/5] Packaging .pkpass..."
rm -f "$PKPASS"
cd "$PASS_DIR" && zip -r "$PKPASS" * > /dev/null
SIZE=$(ls -lh "$PKPASS" | awk '{print $5}')
echo "  $PKPASS ($SIZE)"

# 4. Upload + invalidate
echo "[4/5] Uploading to S3 + invalidating CloudFront..."
aws s3 cp "$PKPASS" "s3://$BUCKET/JamesTannahill.pkpass" \
  --content-type "application/vnd.apple.pkpass" \
  --cache-control "max-age=3600" > /dev/null 2>&1
aws cloudfront create-invalidation \
  --distribution-id "$CF_DIST" \
  --paths "/JamesTannahill.pkpass" > /dev/null 2>&1
echo "  Uploaded and cache invalidated"

# 5. Push to all devices
echo "[5/5] Pushing update to registered devices..."
python3 "$SCRIPT_DIR/pass-service/push_update.py"

echo ""
echo "=== Done ==="
