# jamestannahill-map

Static pages for `map.jamestannahill.com` and `contact.jamestannahill.com` — a Mapbox map and tactical digital business card for James Tannahill.

## Pages

### map.jamestannahill.com
Dark-themed Mapbox GL JS map centered on W 57th Street, Manhattan. Plocamium Holdings marker with popup. Cinematic fly-in animation. Links to contact page.

### contact.jamestannahill.com
Tactical HUD-style digital business card. Neue Haas Grotesk + JetBrains Mono. Features:

- **Contact links** — Email, Signal (redacted/tap-to-reveal), WhatsApp (redacted/tap-to-reveal), LinkedIn, GitHub, Bloomberg, art.jamestannahill.com
- **Ventures grid** — Plocamium, 1nessAgency, HLTHvrs, MonkeyThorn, gOOOvy, NewYorkLab, HMU API, RDLB
- **vCard download** — saves contact to phone (Signal + WhatsApp URLs included)
- **QR code** — tactical dark theme with gold modules, crosshairs, corner brackets. Tap to fullscreen (white overlay, wake lock)
- **Share** — shares QR as PNG image via native share sheet
- **SEO** — Person schema (JSON-LD), OG + Twitter cards

## Infrastructure

- **Hosting:** S3 + CloudFront (us-east-1)
- **DNS:** Cloudflare CNAMEs → CloudFront
- **SSL:** ACM certificates (DNS-validated)

| Subdomain | S3 Bucket | CloudFront ID |
|-----------|-----------|---------------|
| map.jamestannahill.com | map.jamestannahill.com | EBLKZPTH1FBUA |
| contact.jamestannahill.com | contact.jamestannahill.com | E28BIZ72OMRUET |

## Deploy

```bash
# Map page
aws s3 cp index.html s3://map.jamestannahill.com/index.html --content-type "text/html"
aws cloudfront create-invalidation --distribution-id EBLKZPTH1FBUA --paths "/*"

# Contact page
aws s3 cp contact.html s3://contact.jamestannahill.com/index.html --content-type "text/html"
aws cloudfront create-invalidation --distribution-id E28BIZ72OMRUET --paths "/*"
```

## Files

- `index.html` — Map page (Mapbox GL JS)
- `contact.html` — Contact/business card page
- `cf-config.json` — CloudFront distribution config (map)
- `cf-contact-config.json` — CloudFront distribution config (contact)
