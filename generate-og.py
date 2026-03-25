#!/usr/bin/env python3
"""Generate a 1200x630 OG image for social sharing."""

import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = (6, 6, 6)
GOLD = (201, 168, 76)
GOLD_DIM = (139, 115, 50)
TEXT_LIGHT = (216, 212, 204)
GRAY = (74, 74, 74)

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# --- Grain / noise texture ---
random.seed(42)
pixels = img.load()
for y in range(H):
    for x in range(W):
        noise = random.randint(-8, 8)
        r, g, b = pixels[x, y]
        pixels[x, y] = (
            max(0, min(255, r + noise)),
            max(0, min(255, g + noise)),
            max(0, min(255, b + noise)),
        )

# --- Fonts ---
font_name = ImageFont.truetype(FONT_PATH, size=60, index=7)       # Light
font_subtitle = ImageFont.truetype(FONT_PATH, size=18, index=7)   # Light
font_coords = ImageFont.truetype(FONT_PATH, size=14, index=7)     # Light
font_tiny = ImageFont.truetype(FONT_PATH, size=10, index=0)       # Regular
font_bracket = ImageFont.truetype(FONT_PATH, size=18, index=7)    # Light

# --- Gold horizontal rule near top center ---
rule_y = 230
rule_w = 32
draw.line(
    [(W // 2 - rule_w // 2, rule_y), (W // 2 + rule_w // 2, rule_y)],
    fill=GOLD,
    width=1,
)

# --- "James Tannahill" ---
name_text = "James Tannahill"
name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
name_w = name_bbox[2] - name_bbox[0]
draw.text(
    ((W - name_w) // 2, rule_y + 20),
    name_text,
    fill=TEXT_LIGHT,
    font=font_name,
)

# --- "INTELLIGENT CAPITAL · xAI" ---
subtitle_text = "INTELLIGENT CAPITAL  ·  xAI"
subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
subtitle_w = subtitle_bbox[2] - subtitle_bbox[0]
draw.text(
    ((W - subtitle_w) // 2, rule_y + 92),
    subtitle_text,
    fill=GOLD_DIM,
    font=font_subtitle,
)

# --- Coordinates ---
coords_text = "40.765°N  ·  73.977°W  ·  NYC"
coords_bbox = draw.textbbox((0, 0), coords_text, font=font_coords)
coords_w = coords_bbox[2] - coords_bbox[0]
draw.text(
    ((W - coords_w) // 2, rule_y + 122),
    coords_text,
    fill=GRAY,
    font=font_coords,
)

# --- Corner brackets ---
BRACKET_LEN = 28
BRACKET_WEIGHT = 1
MARGIN = 36


def draw_bracket(corner: str):
    if corner == "tl":
        x0, y0 = MARGIN, MARGIN
        draw.line([(x0, y0), (x0 + BRACKET_LEN, y0)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
        draw.line([(x0, y0), (x0, y0 + BRACKET_LEN)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
    elif corner == "tr":
        x0, y0 = W - MARGIN, MARGIN
        draw.line([(x0, y0), (x0 - BRACKET_LEN, y0)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
        draw.line([(x0, y0), (x0, y0 + BRACKET_LEN)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
    elif corner == "bl":
        x0, y0 = MARGIN, H - MARGIN
        draw.line([(x0, y0), (x0 + BRACKET_LEN, y0)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
        draw.line([(x0, y0), (x0, y0 - BRACKET_LEN)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
    elif corner == "br":
        x0, y0 = W - MARGIN, H - MARGIN
        draw.line([(x0, y0), (x0 - BRACKET_LEN, y0)], fill=GOLD_DIM, width=BRACKET_WEIGHT)
        draw.line([(x0, y0), (x0, y0 - BRACKET_LEN)], fill=GOLD_DIM, width=BRACKET_WEIGHT)


for c in ("tl", "tr", "bl", "br"):
    draw_bracket(c)

# --- "// SECURE CHANNEL" top-left ---
draw.text(
    (MARGIN + 4, MARGIN + 8),
    "// SECURE CHANNEL",
    fill=GRAY,
    font=font_tiny,
)

# --- Save ---
out_path = "/Users/jamest/jamestannahill-map/og-image.png"
img.save(out_path, "PNG")
print(f"Saved {W}x{H} OG image to {out_path}")
