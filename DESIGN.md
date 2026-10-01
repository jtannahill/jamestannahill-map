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
  bg: "#ffffff"
  bg-lift: "#f8f8f8"
typography:
  mono:
    fontFamily: JetBrains Mono
---

# contact.jamestannahill.com

## Overview

A digital business card at contact.jamestannahill.com, served from `contact.html` in this repository. The README describes it as a Bloomberg editorial card; the visual direction is a tactical HUD: a near-black sticky topbar with a red rule and coordinates readout, then a white single column of monospaced, uppercase, letter-spaced labels, hairline dividers, and red used only as a signal color.

Scope: this document governs the contact card only (`contact.html`). The repository also holds `map/`, which is the separate map.jamestannahill.com site, and supporting pages (`add.html`, `404.html`) that define their own tokens. None of those are covered here.

## Colors

- `red` is a signal, not a fill. Use it for the topbar bottom rule, the hero eyebrow, link arrows, the featured row's left border, the subscribed push state, QR corner brackets and crosshairs, and the toast top rule. Never use it as a large background.
- `ink` is both the primary text color and the only dark surface (topbar, toast, skip link). Text on `ink` is white.
- `muted` is the floor for small labels on white. It was darkened for contrast; do not reintroduce a lighter gray for text.
- Icons in link rows and the topbar coordinates use `#949494`, which sits on the dark topbar and as decorative glyphs next to labeled text. Keep that value to those two roles; do not use it for readable text on white.
- `rule` draws every hairline: section header rules, row dividers, and the 1px gaps of the ventures and actions grids (a `rule` background behind `bg` cells).
- `bg-lift` is the pressed and hovered surface for rows, cards, and action buttons, and the QR canvas background.
- The page is light only. There is no dark theme; `theme-color` matches `ink` so the browser chrome continues the topbar.

## Typography

- Everything is set in `mono` (JetBrains Mono, weights 300 to 700 loaded from Google Fonts). Do not introduce a second family on this page; the Bloomberg "B" glyph in the link list is a one-off icon, not a text face.
- Labels, section headers, eyebrows, and button text are uppercase with positive letter-spacing. Display text (the hero name, venture names) is bold with negative letter-spacing.
- Weight carries hierarchy: 700 for the name, section headers, and eyebrow; 600 for venture names; 500 for the topbar name and action buttons; 400 in `text` for the hero role line.
- Size floor: uppercase labels (eyebrow, section headers, link labels, QR label, overlay label, venture flag) are at least 10px; values, descriptions, buttons, hints, links, and the toast are at least 11px. Keep the HUD feel with tracking and weight, never by shrinking below the floor.
- Channel values that can be long (emails, URLs) must wrap with `overflow-wrap: anywhere` rather than truncate.

## Layout

- One column, max width 480px, centered. Sections are full-bleed inside that column, separated by hairline rules rather than spacing or cards.
- Horizontal gutter is 20px, dropping to 16px at 480px and below; the topbar respects safe-area insets on all sides.
- Section order: topbar, hero, Contact, Ventures, Actions, QR, footer. Each section after the hero opens with a section header: uppercase name plus a flexible hairline. There is no data strip; it only repeated the eyebrow and address.
- Actions: Save Contact first, then Add to Apple Wallet, then Get Updates (only where push is supported). There is no View Map action; the hero address already links to the map.
- Ventures and actions are two-column grids; an odd last item spans both columns. When a cell is unsupported (web push outside an installed iOS web app), remove the element so no empty cell remains.
- Touch targets on mobile are at least 44px (48px for link rows and action buttons), including the hero address link and footer links.

## Elevation & Depth

- The page is flat: no shadows. Depth comes only from the sticky topbar, the full-screen QR overlay (near-opaque white scrim), and the toast.
- Motion is small and optional. Section reveal (8px rise and fade) runs only under `(scripting: enabled) and (prefers-reduced-motion: no-preference)`, so content is never hidden when JavaScript is off. Smooth scrolling and view transitions are disabled under reduced motion. Revealed sections are forced visible for print. There is no device-orientation tilt and the page never requests motion permission.

## Shapes

- Corners are square everywhere. Do not add border radii to rows, cards, buttons, the overlay button, or the toast.
- Accents are drawn with 1px or 2px lines: 2px for the topbar rule, featured-row border, and toast rule; 1px for dividers, QR buttons, and QR corner brackets.

## Components

- Link row: icon, fixed-width uppercase label, value, red arrow. The featured row (email) adds a 2px red left border and reduces left padding by the same amount. Rows that act rather than navigate are `<button type="button">` elements styled identically to the anchors.
- Redacted row (Signal, WhatsApp): the value shows block characters in `muted` and a `muted` arrow. The first tap reveals the value, turns the arrow red, updates the button's accessible name, and shows a toast; the second tap opens the channel.
- QR block: canvas framed by four red corner brackets at half opacity. Activating it (click, Enter, Space) opens the overlay.
- QR overlay: a modal dialog (`role="dialog"`, `aria-modal`) that is `inert` and `aria-hidden` while closed. Opening moves focus to the Close button and requests a screen wake lock; closing by the Close button, a tap anywhere, or Escape releases the wake lock and returns focus to the trigger.
- Toast: `ink` bar with a red top rule, bottom-centered, `role="status"` with polite live announcements, auto-dismissed after 2.5s. Use it as the single feedback channel for copy, share, download, and push state.
- Focus: every focusable element shows `:focus-visible { outline: 2px solid var(--ink); outline-offset: -2px; }`.
- Link row dividers are 1px `rule` on every row except the last row of `#links`.
- Former roles are marked with a `venture-flag` ("Former") next to the venture name. Plocamium Holdings is a former role; the current role is AI/ML for Capital Markets at SpaceXAI.
- Hover states apply only under `(hover: hover) and (pointer: fine)`; touch devices get `:active` feedback instead. Keep new hover rules inside that query.

## Do's and Don'ts

- Do update the Content Security Policy whenever you change any inline `<script>` block or any `onclick` attribute value in `contact.html`. Those scripts are allowlisted by sha256 hashes in CloudFront response headers policy `contact-jamestannahill-security-csp` (ID `25fe67ef-1688-4657-b87a-8138ed0e245b`); inline handlers are covered by `'unsafe-hashes'` plus a per-handler hash. Recompute each changed hash and update that policy before deploying, or the script is blocked in production. Adding a new inline script or handler needs a new hash in the same policy. See the CSP NOTE comment in the `<head>` of `contact.html`.
- Do prefer `addEventListener` in an existing script block over new `onclick` attributes, so that fewer hashes change.

## Open Questions

- None open. Label floor, data strip, action order, and the gyroscope tilt were decided by the owner on 2026-10-01 (see Typography, Layout, and Elevation).
