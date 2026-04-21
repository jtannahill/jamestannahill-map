# jamestannahill-map

[![Built with Mapbox](https://img.shields.io/badge/Built%20with-Mapbox-blue?logo=mapbox)](https://www.mapbox.com)

Static pages and Apple Wallet pass infrastructure for `map.jamestannahill.com` and `contact.jamestannahill.com`.

---

## Pages

### `map.jamestannahill.com`
Dark Mapbox GL JS map centered on W 57th Street, Manhattan. Plocamium Holdings marker with popup, cinematic fly-in animation on load.

### `contact.jamestannahill.com`
Bloomberg editorial digital business card (redesigned Apr 2026). JetBrains Mono. White/black/red palette — black topbar with `#e01a1a` red rule, white body, 3-cell data strip (xAI / NYC / PE·HC).

**Features:**
- Contact links — Email (featured, red left border), Signal (redacted/tap-to-reveal), WhatsApp (redacted/tap-to-reveal), LinkedIn, GitHub, Bloomberg Terminal Profile, Art
- Ventures grid — Plocamium, 1nessAgency, MonkeyThorn, gOOOvy, NewYorkLab, HMU API, RDLB
- vCard download — saves contact to phone with all channels
- QR code — MECARD format, dark modules on light bg, red crosshairs, fullscreen overlay on tap
- Apple Wallet pass — add to Wallet via button or NFC physical card
- Gyroscope parallax — subtle tilt effect on mobile
- PWA — installable, service worker cached, offline-capable
- Web push — opt-in `// Subscribed` button (shows when supported)
- SEO — Person schema (JSON-LD), OG + Twitter cards

### `contact.jamestannahill.com/add`
NFC landing page — device-aware router for the physical business card NFC chip.

| Device + Browser | Behavior |
|---|---|
| iPhone + Safari | Auto-redirects to `.pkpass` — Wallet opens in ~1 second |
| iPhone + Chrome/other | Shows "Open in Safari" with direct link |
| Android | Shows contact card link |
| Desktop | Shows "Scan on iPhone" message |

---

## Apple Wallet Pass

Pass type: `pass.com.jamestannahill.contact` — Team `P3ZC6ZG46V`

**Pass features:**
- Generic pass — name, title, org, email, coordinates
- Back fields — Signal, WhatsApp, LinkedIn, GitHub, Bloomberg, all venture links
- MECARD QR barcode — scannable to save contact
- Location relevance — surfaces on lock screen near W 57th St, NYC
- Web service — live push updates via APNs when pass content changes
- Device registration — DynamoDB (`wallet-pass-registrations`)

### Pass Update Pipeline

Edit `pass-build/pass.pass/pass.json`, then run:

```bash
./update-pass.sh
```

This does five things in sequence:
1. Rebuilds `manifest.json` (SHA-1 hash of every file)
2. Signs with `~/pass-cert.pem` + `~/pass-key.pem` against WWDR
3. Packages into `JamesTannahill.pkpass`
4. Uploads to S3 + invalidates CloudFront cache
5. Sends silent APNs push to all registered devices — Wallet fetches the new pass automatically

### Manual Push Only

```bash
python3 pass-service/push_update.py
```

### Pass Certificate

- File: `~/pass-cert.pem` + `~/pass-key.pem`
- Valid until: **Apr 25, 2027**
- Same certificate signs the pass and sends APNs push — no separate push cert needed

---

## Physical NFC Business Card

The `/add` landing page is designed for an NFC chip embedded in a physical business card.

**Chip:** NTAG213 (144 bytes — URL fits with 70+ bytes to spare)

**URL written to chip:**
```
https://contact.jamestannahill.com/add
```

**Writing with Flipper Zero (Momentum firmware):**
```
NFC → Saved → [tag] → Write
  → hold blank NTAG213 to Flipper back (top third — NFC antenna)
  → vibration = success
  → repeat for each card
```

**Test before writing physical cards:**
```
NFC → Saved → [tag] → Emulate
  → hold Flipper to iPhone — banner appears — tap — Wallet opens
```

**Card format recommendation:** Matte black metal (aluminum) with gold laser engraving, NTAG213 embedded with booster antenna. Flipper writes to the antenna corner.

**Tap flow (iPhone + Safari as default browser):**
```
Tap iPhone to card
  → banner appears (~1 second)
  → user taps banner
  → /add page loads, detects Safari
  → auto-redirects to .pkpass
  → Wallet opens with "Add to Apple Wallet"
  → one tap — pass saved
```

---

## Infrastructure

| Subdomain | S3 Bucket | CloudFront ID |
|---|---|---|
| map.jamestannahill.com | map.jamestannahill.com | EBLKZPTH1FBUA |
| contact.jamestannahill.com | contact.jamestannahill.com | E28BIZ72OMRUET |

- **DNS:** Cloudflare CNAMEs → CloudFront
- **SSL:** ACM certificates (DNS-validated)
- **Pass web service:** Lambda + API Gateway + DynamoDB (separate CDK stack)
- **Push:** APNs HTTP/2 via `httpx`, certificate auth

## Deploy

```bash
# Map page
aws s3 cp index.html s3://map.jamestannahill.com/index.html --content-type "text/html"
aws cloudfront create-invalidation --distribution-id EBLKZPTH1FBUA --paths "/*"

# Contact page
aws s3 cp contact.html s3://contact.jamestannahill.com/index.html --content-type "text/html"
aws cloudfront create-invalidation --distribution-id E28BIZ72OMRUET --paths "/*"

# NFC landing page
aws s3 cp add.html s3://contact.jamestannahill.com/add --content-type "text/html"
aws cloudfront create-invalidation --distribution-id E28BIZ72OMRUET --paths "/add"

# Wallet pass (full pipeline)
./update-pass.sh
```

## Files

```
index.html              Map page (Mapbox GL JS)
contact.html            Contact/business card page
add.html                NFC landing page — device-aware Wallet pass router
sw.js                   Service worker (PWA + offline cache)
manifest.json           PWA manifest
og-image.png            OG social preview image

pass-build/
  pass.pass/            Pass bundle (edit pass.json here)
    pass.json           Pass definition — fields, locations, web service URL
    manifest.json       Auto-generated SHA-1 manifest (do not edit)
    signature           Auto-generated PKCS#7 signature (do not edit)
    *.png               Pass imagery (icon, logo, thumbnail)
  JamesTannahill.pkpass Signed pass (built by update-pass.sh)

pass-service/
  handler.py            Lambda — Apple Wallet web service (register/unregister/serve/log)
  push_update.py        APNs push — notifies all registered devices to fetch updated pass

update-pass.sh          Full pass pipeline — rebuild, sign, upload, invalidate, push
```
