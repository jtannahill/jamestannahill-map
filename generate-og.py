#!/usr/bin/env python3
"""Generate the two 1200x630 link-preview images.

og-image.png      contact.jamestannahill.com: the card's own hero (off-white,
                  ink band with the red rule, red role lines, stacked name in
                  JetBrains Mono), so the preview looks like the page it opens.
map/og-image.png  map.jamestannahill.com: the dark-v11 map of New York under a
                  neutral scrim, name in NHG Display Light. No pin and no
                  coordinates (owner decision 2026-10-30).

Run: uv run --with pillow python generate-og.py
JetBrains Mono (OFL) ships in og/fonts. NHG Display is licensed and stays in
/Library/Fonts. og/map-base.png is a Mapbox Static Images render, kept with its
Mapbox logo and attribution; refetch it with the URL in og/map-base.url.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OG = ROOT / "og"
SCALE = 2
W, H = 1200, 630

ROLE = "VP of Super Intelligence Innovation"
EMPLOYER = "Atlas SP Partners, an Apollo company"
FIRST, LAST = "James", "Tannahill"

MONO_BOLD = OG / "fonts" / "JetBrainsMono-Bold.ttf"
NHG_LIGHT = Path("/Library/Fonts/NeueHaasDisplayLight.ttf")
NHG_ROMAN = Path("/Library/Fonts/NeueHaasDisplayRoman.ttf")


def font(path, size):
    return ImageFont.truetype(str(path), size=round(size * SCALE))


def text_width(text, f, tracking):
    """Advance width with per-letter tracking (in em), no trailing tracking."""
    extra = tracking * f.size
    return sum(f.getlength(c) for c in text) + extra * (len(text) - 1)


def draw_text(draw, xy, text, f, fill, tracking=0.0):
    x, y = xy
    if not tracking:
        draw.text((x, y), text, font=f, fill=fill, anchor="ls")
        return
    extra = tracking * f.size
    for c in text:
        draw.text((x, y), c, font=f, fill=fill, anchor="ls")
        x += f.getlength(c) + extra


def cap_height(f):
    return -f.getbbox("H", anchor="ls")[1]


def contact_card():
    """Tokens from DESIGN.md: bg #fdfdfc, ink #1a1a1a, red #e01a1a."""
    bg, ink, red = (253, 253, 252), (26, 26, 26), (224, 26, 26)
    img = Image.new("RGB", (W * SCALE, H * SCALE), bg)
    d = ImageDraw.Draw(img)

    band, rule = 72 * SCALE, 6 * SCALE
    d.rectangle((0, 0, W * SCALE, band), fill=ink)
    d.rectangle((0, band, W * SCALE, band + rule), fill=red)

    eyebrow = font(MONO_BOLD, 32)
    name = font(MONO_BOLD, 150)
    eyebrow_track, name_track = 0.08, -0.02
    x = 96 * SCALE

    eyebrow_lead = round(eyebrow.size * 1.5)
    name_lead = round(name.size * 0.98)
    gap = 44 * SCALE
    block = cap_height(eyebrow) + eyebrow_lead + gap + cap_height(name) + name_lead
    top = band + rule + ((H * SCALE - band - rule) - block) // 2 - 8 * SCALE

    y = top + cap_height(eyebrow)
    draw_text(d, (x, y), ROLE.upper(), eyebrow, red, eyebrow_track)
    draw_text(d, (x, y + eyebrow_lead), EMPLOYER.upper(), eyebrow, red, eyebrow_track)

    y += eyebrow_lead + gap + cap_height(name)
    draw_text(d, (x, y), FIRST, name, ink, name_track)
    draw_text(d, (x, y + name_lead), LAST, name, ink, name_track)

    widest = max(text_width(s, f, t) for s, f, t in (
        (ROLE.upper(), eyebrow, eyebrow_track),
        (LAST, name, name_track),
    ))
    assert x + widest < (W - 96) * SCALE, "contact text runs into the right margin"
    return img.resize((W, H), Image.LANCZOS)


def map_card():
    """Tokens from map/DESIGN.md: ink #0A0A0A, paper #E8E4DC, gold-text #A88B3F."""
    ink, paper, gold_text = (10, 10, 10), (232, 228, 220), (168, 139, 63)
    base = Image.open(OG / "map-base.png").convert("RGB").resize((W * SCALE, H * SCALE), Image.LANCZOS)

    # Neutral scrim under the type (the one sanctioned gradient): solid ink at
    # 88% across the text column, easing to clear by 66% of the width so
    # Manhattan stays untouched.
    scrim = Image.new("L", base.size, 0)
    sd = ImageDraw.Draw(scrim)
    solid, clear = 0.46 * base.width, 0.66 * base.width
    for px in range(base.width):
        a = 0.88 if px <= solid else max(0.0, 0.88 * (1 - (px - solid) / (clear - solid)))
        sd.line((px, 0, px, base.height), fill=round(a * 255))
    img = Image.composite(Image.new("RGB", base.size, ink), base, scrim)
    d = ImageDraw.Draw(img)

    name = font(NHG_LIGHT, 132)
    role = font(NHG_ROMAN, 36)
    x = 96 * SCALE
    name_lead = round(name.size * 0.98)
    role_lead = round(role.size * 1.4)
    gap = 48 * SCALE
    block = cap_height(name) + name_lead + gap + cap_height(role) + role_lead
    top = (H * SCALE - block) // 2 - 8 * SCALE

    y = top + cap_height(name)
    draw_text(d, (x, y), FIRST, name, paper, -0.01)
    draw_text(d, (x, y + name_lead), LAST, name, paper, -0.01)
    y += name_lead + gap + cap_height(role)
    draw_text(d, (x, y), ROLE, role, gold_text)
    draw_text(d, (x, y + role_lead), EMPLOYER, role, paper)
    return img.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    outputs = (
        (contact_card(), ROOT / "og-image.png"),
        (map_card(), ROOT / "map" / "og-image.jpg"),
    )
    for image, path in outputs:
        if path.suffix == ".jpg":
            image.save(path, "JPEG", quality=86, optimize=True, progressive=True)
        else:
            image.save(path, "PNG", optimize=True)
        print(f"Saved {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")
