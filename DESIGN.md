---
version: alpha
name: contact.jamestannahill.com
description: Tactical HUD digital business card for James Tannahill, a single light-theme mobile-first page in JetBrains Mono with a near-black topbar and a red accent.
colors:
  red: "#e01a1a"
  ink: "#1a1a1a"
  text: "#333333"
  muted: "#6b6b6b"
  rule: "#e0e0e0"
  bg: "#fdfdfc"
  on-ink: "#f5f5f3"
  bg-lift: "#f8f8f8"
  bg-press: "#ececec"
typography:
  mono:
    fontFamily: JetBrains Mono
---

# contact.jamestannahill.com

## Overview

A digital business card at contact.jamestannahill.com, served from `contact.html` in this repository. The README describes it as a Bloomberg editorial card; the visual direction is a tactical HUD: a near-black sticky topbar with a red rule and coordinates readout, then a white single column of monospaced, uppercase, letter-spaced labels, hairline dividers, and red used only as a signal color.

Scope: this document governs the contact card only (`contact.html`). The repository also holds `map/`, which is the separate map.jamestannahill.com site, and supporting pages (`add.html`, `404.html`) that define their own tokens. None of those are covered here.

## Colors

- `red` is a signal, not a fill. Use it for the topbar bottom rule, the hero eyebrow, link arrows, and the toast top rule. Never use it as a large background.
- `ink` is both the primary text color and the only dark surface (topbar, toast, skip link). Text on `ink` is `on-ink`, an off-white; the page background is the off-white `bg`. Pure white is kept only for the QR overlay scrim and canvas, so the code scans.
- `muted` is the floor for small labels on white. It was darkened for contrast; do not reintroduce a lighter gray for text.
- Icons in link rows use `#949494`, as decorative glyphs next to labeled text. Do not use it for readable text on white.
- `rule` draws every hairline: the hero's bottom rule, row dividers, the line above the actions, and the 1px gap of the actions grid (a `rule` background behind `bg` cells).
- `bg-lift` is the hovered surface for rows and action buttons. `bg-press` is the pressed surface: `bg-lift` is only 1.06:1 against white, too faint to see on a bright phone.
- The page is light only and says so (`color-scheme: light`), so browser auto-dark modes leave it, and the QR, alone.
- The page is light only. There is no dark theme; `theme-color` matches `ink` so the browser chrome continues the topbar.

## Typography

- Everything is set in `mono` (JetBrains Mono, weights 400, 500 and 700 loaded from Google Fonts; load nothing unused). Do not introduce a second family on this page; the Bloomberg "B" glyph in the link list is a one-off icon, not a text face.
- Labels, eyebrows, and button text are uppercase with positive letter-spacing. Display text (the hero name) is bold with negative letter-spacing.
- Weight carries hierarchy: 700 for the name and eyebrow; 500 for the QR button and action buttons.
- Size floor: uppercase labels (eyebrow, link labels, overlay label) are at least 10px; values, buttons, hints, links, and the toast are at least 11px. Keep the HUD feel with tracking and weight, never by shrinking below the floor.
- Channel values that can be long (emails, URLs) must wrap with `overflow-wrap: anywhere` rather than truncate.

## Layout

- One column, max width 480px, centered. Sections are full-bleed inside that column, separated by hairline rules rather than spacing or cards.
- Horizontal gutter is 20px, dropping to 16px at 480px and below; the topbar respects safe-area insets on all sides.
- Less is more: the card is gate-kept. Order: topbar (QR button only, no name), hero (eyebrow and name only), contact rows (Email, Signal, WhatsApp, LinkedIn), actions, footer. There are no visible section headers (the `h2`s are visually hidden), no address or coordinates, no ventures grid, no extra profiles, and no inline QR block. Do not add them back without the owner asking (decided 2026-10-24). The saved vCard and the QR's MECARD carry the same short set: no address, no venture links.
- Actions: Save Contact, then Add to Apple Wallet (Apple devices only). There is no Get Updates or View Map action.
- Actions are a two-column grid; an odd last item spans both columns. Off Apple devices the Wallet badge is removed, so Save Contact spans the row.
- Touch targets are at least 44px (48px for link rows and action buttons), including footer links. They follow `pointer: coarse`, not width, so landscape phones and tablets get them too.
- The topbar content aligns with the 480px column and holds only the QR button at the right edge, so the code is one tap away when showing the card in person. The name is not repeated there.
- The eyebrow sets the role and the employer on two lines (one `span` each), so the company name never breaks mid-name.
- The page fills the screen (body and `.page` are flex columns) and the footer takes `margin-top: auto`, so it sits at the bottom of the screen rather than mid-page.

## Elevation & Depth

- The page is flat: no shadows. Depth comes only from the sticky topbar, the full-screen QR overlay (near-opaque white scrim), and the toast.
- Motion is small and optional. Section reveal (8px rise and fade) runs only under `(scripting: enabled) and (prefers-reduced-motion: no-preference)`, so content is never hidden when JavaScript is off. Smooth scrolling and view transitions are disabled under reduced motion. Revealed sections are forced visible for print. There is no device-orientation tilt and the page never requests motion permission.

## Shapes

- Corners are square everywhere. Do not add border radii to rows, cards, buttons, the overlay button, or the toast.
- Accents are drawn with 1px or 2px lines: 2px for the topbar rule and toast rule; 1px for dividers.

## Components

- Link row: icon, fixed-width uppercase label, value, red arrow. All rows are equal; there is no featured row and no side stripe (a banned pattern). Rows that act rather than navigate are `<button type="button">` elements styled identically to the anchors.
- Redacted row (Signal, WhatsApp): the value shows block characters in `muted` and a `muted` arrow. The first tap reveals the value, turns the arrow red, updates the button's accessible name, and shows a toast; the second tap opens the channel.
- QR: the topbar QR button opens the overlay; `card.js` loads the QR library on every visit for it. The canvas is drawn at whole device pixels per module and never scaled by CSS, so the code stays sharp.
- QR overlay: a modal dialog (`role="dialog"`, `aria-modal`) that is `inert` and `aria-hidden` while closed. The hint reads "Tap anywhere to close" on touch and "Click anywhere or press Escape" with a fine pointer. Opening moves focus to the Close button and requests a screen wake lock; closing by the Close button, a tap anywhere, or Escape releases the wake lock and returns focus to the trigger. While open, the page behind is `inert`; the wake lock is requested again when the tab becomes visible.
- Script-only controls (Signal, WhatsApp, the topbar QR button) are `hidden` in markup and shown by `card.js`. Save Contact is a plain link to the static `/James_Tannahill.vcf`, so it works without script. All behaviour lives in `card.js` and `add.js`; the pages carry no inline scripts or `on*` attributes, so the CSP needs no hashes.
- Toast: `ink` bar with a red top rule, bottom-centered, `role="status"` with polite live announcements, auto-dismissed after 2.5s. Use it as the single feedback channel for download and reveal feedback.
- Focus: every focusable element shows `:focus-visible { outline: 2px solid var(--ink); outline-offset: -2px; }`.
- Link row dividers are 1px `rule` on every row except the last row of `#links`; the actions grid draws its own top rule.
- The current role is AI/ML for Capital Markets at SpaceX Super Intelligence, shown only as the hero eyebrow.
- Hover states apply only under `(hover: hover) and (pointer: fine)`; touch devices get `:active` feedback instead. Keep new hover rules inside that query.

## Do's and Don'ts

- Do update the Content Security Policy whenever you change any inline `<script>` block or any `onclick` attribute value in `contact.html`. Those scripts are allowlisted by sha256 hashes in CloudFront response headers policy `contact-jamestannahill-security-csp` (ID `25fe67ef-1688-4657-b87a-8138ed0e245b`); inline handlers are covered by `'unsafe-hashes'` plus a per-handler hash. Recompute each changed hash and update that policy before deploying, or the script is blocked in production. Adding a new inline script or handler needs a new hash in the same policy. See the CSP NOTE comment in the `<head>` of `contact.html`.
- Do prefer `addEventListener` in an existing script block over new `onclick` attributes, so that fewer hashes change.

## Open Questions

- None open. Label floor, data strip, action order, and the gyroscope tilt were decided by the owner on 2026-10-01 (see Typography, Layout, and Elevation).
