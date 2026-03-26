from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/Users/jamest/Library/Fonts/Avenir LT Std 85 Heavy.otf"
OUT_DIR = "/Users/jamest/jamestannahill-map"
BG = "#060606"
GOLD = "#C9A84C"
GOLD_DIM = "#8B7332"


def generate_favicon():
    scale = 3
    size = 32 * scale  # 96x96
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 18 * scale)
    bbox = draw.textbbox((0, 0), "JT", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), "JT", fill=GOLD, font=font)
    img = img.resize((32, 32), Image.LANCZOS)
    img.save(f"{OUT_DIR}/favicon.png")
    print("favicon.png saved (32x32)")


def generate_apple_touch_icon():
    scale = 3
    size = 180 * scale  # 540x540
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 80 * scale)
    bbox = draw.textbbox((0, 0), "JT", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    draw.text((x, y), "JT", fill=GOLD, font=font)
    # 1px border at final size = 3px at render size
    draw.rectangle([0, 0, size - 1, size - 1], outline=GOLD_DIM, width=3)
    img = img.resize((180, 180), Image.LANCZOS)
    img.save(f"{OUT_DIR}/apple-touch-icon.png")
    print("apple-touch-icon.png saved (180x180)")


if __name__ == "__main__":
    generate_favicon()
    generate_apple_touch_icon()
