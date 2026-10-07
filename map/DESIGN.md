---
version: alpha
name: map.jamestannahill.com
description: Single-screen noir map for James Tannahill, a Mapbox dark-v11 canvas with a gold Plocamium marker, a cinematic fly-in and a centred name card in NHG Display.
colors:
  gold: "#C9A84C"
  gold-dim: "#8B7332"
  gold-text: "#A88B3F"
  ink: "#0A0A0A"
  smoke: "#1A1A1A"
  ash: "#8C8C8C"
  paper: "#E8E4DC"
  paper-dim: "#B8B4AC"
typography:
  display:
    fontFamily: NHG Display
    weights: [300, 400, 500, 700]
---

# map.jamestannahill.com

## Overview

One non-scrolling screen (`map/index.html`, deployed with `aws s3 sync map/`). A dark Mapbox map flies from New Jersey to the Plocamium Holdings pin at 9 W 57th St, then a name card, wordmark and coordinates chip settle over it. The map is the content; everything else is quiet chrome. This file does not cover `contact.html` (see the root DESIGN.md).

## Location

The pin is the Plocamium Holdings, LLC Google place: `[-73.9749, 40.7636]` (place id `0x89c259b3cfa546fd:0x95a7db7a8397714f`, short link https://maps.app.goo.gl/XjUupgjudiNXR4S2A). The same coordinates appear in the `PLOCAMIUM` constant, the JSON-LD `geo`, the coordinates chip (40.764 N, 73.975 W) and `llms.txt`. Change all of them together.

## Colors

- Ink `#0A0A0A` page background; smoke `#1A1A1A` popup and reduced-transparency surfaces.
- Gold `#C9A84C` marks interactive things only: marker, CTA, popup link, focus rings.
- `#A88B3F` is the coordinates text (static, so a step down from gold). Text over the map sits on a solid scrim (coords chip `rgba(10,10,10,0.75)`, no backdrop blur; card gradient 0.72) or carries a dark `text-shadow`, because road labels behind it are light enough to break 4.5:1 on their own.
- The page declares `color-scheme: dark`, sets body text to paper and themes `::selection`. There is no grain layer (at 3% it was invisible). Scroll and pinch zoom are on; a wheel during the fly-in cancels it.
- `--gold-dim` `#8B7332` is decoration only (the card rule). Never text.
- Ash `#8C8C8C` for small caps labels; the old `#6B6B6B` failed 4.5:1.
- Paper `#E8E4DC` for the name; secondary chrome sits at 0.6 opacity of paper, not lower.

## Typography

NHG Display from fonts.jamestannahill.com, faces 300/400/500/700 only. Do not use 600 (it synthesizes) or italic (no italic face ships). Name at 48px (36px under 600px) weight 300; labels 11 to 12px uppercase with positive tracking; nothing below 11px.

## Motion

- Map fades in on load; the fly-in is a 3.5s `flyTo` 400ms after load. A touch or mousedown before it starts cancels it.
- Card, wordmark and coords use CSS keyframes that stay paused until `body.is-landing`, which `map.js` adds when the fly-in ends (at once under reduced motion or when the map fails, with a 6s backstop); they then stagger 0.2s, 0.4s, 0.6s. There is no scroll reveal; the page does not scroll.
- The fly-in and `jumpTo` pass `padding` (card height + 48px at the bottom), so the pin lands in the open space above the card, never under the name link.
- The marker pings three times after landing, then holds still. Hover effects live inside `@media (hover: hover) and (pointer: fine)`; press states drop links to 0.6 opacity (the CTA also scales to 0.97), and a passive `touchstart` listener makes `:active` fire on iOS.
- Hover transitions animate `transform`, plus `opacity` and `border-color` at 160ms on the strong ease-out (`cubic-bezier(0.23, 1, 0.32, 1)`).
- `prefers-reduced-motion`: `jumpTo` instead of `flyTo`, no ping, no entrance animations, no map fade.

## Layout

- Overlays offset with `env(safe-area-inset-*)`; the viewport has `viewport-fit=cover`.
- `.card` is `pointer-events: none` with its links re-enabled, so the map can be dragged through the card band.
- The privacy link sits centred under the CTA, clear of the Mapbox attribution control at bottom right.
- Minimum 44px targets on the popup close button; the JT wordmark uses padding with a matching negative margin.

## Components

- Marker: a 34px ink disc with a gold ring and "P". `.marker-container` must not set `position`, or it overrides Mapbox's `.mapboxgl-marker { position: absolute }` and the logo detaches from the pin.
- Popup: bound only through `marker.setPopup(popup)`. Do not add a second click listener; it toggles the popup shut.
- Fallback: `.map-fallback` ("Open in Google Maps") shows when JS is off (noscript), when `mapboxgl` failed to load, or when the map constructor throws.

## Accessibility

- Marker `aria-label` names the place; the popup close button has its `aria-hidden` removed on open; Escape closes the popup and returns focus to the marker.
- The attribution button gets `aria-label="Toggle map attribution"`.
- The card is the `main` landmark and the name is the `h1`.
- Gold 2px focus rings with a 4px offset on every link and the marker; on the marker and popup close button a dark 4px halo keeps the ring visible over light map labels.

## Do and do not

- Do keep the role line in the meta description, OG image and contact card in agreement.
- Do not add analytics here; the GA4 tag was removed on 2026-09-17 because it ran without consent gating.
- `sw.js` in this folder is a kill switch that unregisters an old contact-card worker once served on this origin. Keep it; the page itself registers no worker.
