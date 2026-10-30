# jamestannahill-map

![Status](https://img.shields.io/badge/status-live-success)
[![Mapbox](https://img.shields.io/badge/Mapbox-000000?logo=mapbox&logoColor=white)](https://www.mapbox.com)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CloudFront](https://img.shields.io/badge/AWS-CloudFront-FF9900?logo=amazonaws&logoColor=white)
[![Live](https://img.shields.io/badge/live-map.jamestannahill.com-blue)](https://map.jamestannahill.com)
![Last Commit](https://img.shields.io/github/last-commit/jtannahill/jamestannahill-map)

Static pages and Apple Wallet pass infrastructure for `map.jamestannahill.com` and `contact.jamestannahill.com`.

---

## Pages

### `map.jamestannahill.com`
Dark Mapbox GL JS map centered on W 57th Street, Manhattan. Marker with popup at the Plocamium Holdings office (a former role), cinematic fly-in animation on load. Source is `map/`; design rules in `map/DESIGN.md`. Pin = Plocamium Holdings, LLC Google place (9 W 57th St). Falls back to an "Open in Google Maps" link when the map cannot load.

Neither subdomain ships analytics. The GA4 tag (`G-WRDEHD4QYL`, shared with apex `jamestannahill.com`) was removed from both pages on 2026-09-17: it loaded unconditionally, with none of the consent gating the apex applies, and `localStorage` consent does not cross origins. The footer still includes a "privacy" link pointing at the apex policy (`https://www.jamestannahill.com/privacy`).

### `contact.jamestannahill.com`
A gate-kept digital business card, served from `contact.html`. JetBrains Mono, off-white body, near-black topbar with a `#e01a1a` red rule. Design rules and owner decisions live in `DESIGN.md`.

**Features:**
- Hero: role eyebrow and name only
- Contact rows: Email, Signal and WhatsApp (redacted: tap to reveal, tap again to open), LinkedIn
- Save Contact: static vCard (`James_Tannahill.vcf`)
- QR code: MECARD, opened from the topbar button as a full-screen overlay with a wake lock
- Apple Wallet pass: add from the card, or from the NFC landing page (`add.html`)
- Link preview: `og-image.png`, drawn by `generate-og.py`
- PWA: installable, service worker cached, offline-capable
- Web push: opt-in `// Subscribed` button (shows when supported)
- SEO: Person schema (JSON-LD), OG + Twitter cards

### `contact.jamestannahill.com/add`
NFC landing page: device-aware router for the physical business card NFC chip.

| Device + Browser | Behavior |
|---|---|
| iPhone + Safari | Auto-redirects to `.pkpass`: Wallet opens in ~1 second |
| iPhone + Chrome/other | Shows "Open in Safari" with direct link |
| Android | Shows contact card link |
| Desktop | Shows "Scan on iPhone" message |

---

## Apple Wallet Pass

Pass type: `pass.com.jamestannahill.contact`: Team `P3ZC6ZG46V`

**Pass features:**
- Generic pass: name, title, org, email, coordinates
- Back fields: Signal, WhatsApp, LinkedIn, GitHub, Bloomberg, all venture links
- MECARD QR barcode: scannable to save contact
- Location relevance: surfaces on lock screen near W 57th St, NYC
- Web service: live push updates via APNs when pass content changes
- Device registration: DynamoDB (`wallet-pass-registrations`)

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
5. Sends silent APNs push to all registered devices: Wallet fetches the new pass automatically

### Manual Push Only

```bash
python3 pass-service/push_update.py
```

### Pass Certificate

- File: `~/pass-cert.pem` + `~/pass-key.pem`
- Valid until: **Apr 25, 2027**
- Same certificate signs the pass and sends APNs push: no separate push cert needed

---

## Physical NFC Business Card

The `/add` landing page is designed for an NFC chip embedded in a physical business card.

**Chip:** NTAG213 (144 bytes: URL fits with 70+ bytes to spare)

**URL written to chip:**
```
https://contact.jamestannahill.com/add
```

**Writing with Flipper Zero (Momentum firmware):**
```
NFC → Saved → [tag] → Write
  → hold blank NTAG213 to Flipper back (top third: NFC antenna)
  → vibration = success
  → repeat for each card
```

**Test before writing physical cards:**
```
NFC → Saved → [tag] → Emulate
  → hold Flipper to iPhone: banner appears: tap: Wallet opens
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
  → one tap: pass saved
```

---

## Infrastructure

Each subdomain is a static site in its own S3 bucket behind its own CloudFront distribution.

- **DNS:** Cloudflare CNAMEs → CloudFront
- **SSL:** ACM certificates (DNS-validated)
- **Pass web service:** Lambda + API Gateway + DynamoDB (separate CDK stack)
- **Push:** APNs HTTP/2 via `httpx`, certificate auth

## Deploy

```bash
# Placeholders: MAP_BUCKET / CONTACT_BUCKET are the S3 buckets and MAP_DIST /
# CONTACT_DIST the CloudFront distribution IDs for each subdomain.

# Map page. NOTE: the map source lives in map/, NOT the repo root. Deploying
# a root-level page to the map bucket is the Apr-Jun 2026 regression that
# served the contact card on map.jamestannahill.com.
aws s3 sync map/ "s3://$MAP_BUCKET/" --exclude ".*" --exclude "DESIGN.md"
aws cloudfront create-invalidation --distribution-id "$MAP_DIST" --paths "/*"

# Contact page
aws s3 cp contact.html "s3://$CONTACT_BUCKET/index.html" --content-type "text/html"
aws cloudfront create-invalidation --distribution-id "$CONTACT_DIST" --paths "/*"

# NFC landing page
aws s3 cp add.html "s3://$CONTACT_BUCKET/add" --content-type "text/html"
aws cloudfront create-invalidation --distribution-id "$CONTACT_DIST" --paths "/add"

# 404 page (CloudFront serves /404.html for 403 and 404 errors)
aws s3 cp 404.html "s3://$CONTACT_BUCKET/404.html" --content-type "text/html"
aws cloudfront create-invalidation --distribution-id "$CONTACT_DIST" --paths "/404.html"

# Link previews: redraw both, upload, then bump ?v= on og:image/twitter:image
# in contact.html and map/index.html (map/og-image.jpg rides the map sync)
uv run --with pillow python generate-og.py
aws s3 cp og-image.png "s3://$CONTACT_BUCKET/og-image.png" --content-type "image/png"

# Wallet pass (full pipeline)
./update-pass.sh
```

## Files

```
contact.html            Contact/business card page (deploys as the contact bucket's index.html)
card.js                 Contact card behaviour: reveal, QR overlay, wake lock
add.html                NFC landing page: device-aware Wallet pass router
404.html                Not-found page (served by CloudFront for 403/404)
sitemap.xml             Sitemap (lists only the root URL)
sw.js                   Service worker (PWA + offline cache)
manifest.json           PWA manifest
og-image.png            Contact link preview (1200x630), drawn by generate-og.py
generate-og.py          Draws both link previews: og-image.png and map/og-image.jpg
og/                     Generator inputs: JetBrains Mono (OFL) and the Mapbox base map

pass-build/             Repo copy of the pass: pass.json, manifest.json, signature, imagery
JamesTannahill.pkpass   Last signed pass, copied back from ~/pass-build after signing

pass-service/
  handler.py            Lambda: Apple Wallet web service (register/unregister/serve/log)
  push_update.py        APNs push: notifies all registered devices to fetch updated pass

update-pass.sh          Full pass pipeline: rebuild, sign, upload, invalidate, push
```

`update-pass.sh` signs `~/pass-build/pass.pass/`, which is outside this repo. Edit
`pass.json` there as well as in `pass-build/`, and keep nothing else in that folder:
every file in it is zipped into the pass. After signing, copy `manifest.json` and
`signature` back into `pass-build/` and the `.pkpass` into the repo root.
