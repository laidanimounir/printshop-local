import os
from PIL import Image, ImageDraw, ImageFont
import config


def generate_logo():
    size = 512
    img = Image.new('RGBA', (size, size), color=0)
    draw = ImageDraw.Draw(img)

    for y in range(size):
        r = int(107 + (139 - 107) * y / size)
        g = int(63 + (94 - 63) * y / size)
        b = int(31 + (60 - 31) * y / size)
        for x in range(size):
            draw.point((x, y), fill=(r, g, b, 255))

    corner_radius = 40
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=corner_radius, fill=255
    )
    img.putalpha(mask)

    try:
        font_large = ImageFont.truetype("arial.ttf", 160)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text_large = "LP"
    bbox = draw.textbbox((0, 0), text_large, font=font_large)
    tx = (size - (bbox[2] - bbox[0])) // 2
    ty = (size - (bbox[3] - bbox[1])) // 2 - 30
    for dx, dy in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
        draw.text((tx + dx, ty + dy), text_large, font=font_large,
                  fill=(180, 160, 100, 200))
    draw.text((tx, ty), text_large, font=font_large,
              fill=config.COLOR_ACCENT)

    text_small = "LAIDANI PHONE"
    bbox2 = draw.textbbox((0, 0), text_small, font=font_small)
    tx2 = (size - (bbox2[2] - bbox2[0])) // 2
    ty2 = ty + 140
    draw.text((tx2, ty2), text_small, font=font_small,
              fill=(255, 255, 255, 230))

    output_dir = os.path.join(config.BASE_DIR, "static", "images")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "logo.png")
    img.save(output_path)
    print(f"  Logo saved: {output_path}")
    return output_path


def generate_pwa_icons():
    sizes = [192, 512]
    logo_path = os.path.join(config.BASE_DIR, "static", "images", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = generate_logo()

    img = Image.open(logo_path).convert('RGBA')
    output_dir = os.path.join(config.BASE_DIR, "static", "images")
    for size in sizes:
        resized = img.resize((size, size), Image.LANCZOS)
        path = os.path.join(output_dir, f"icon_{size}.png")
        resized.save(path)
        print(f"  PWA icon saved: {path}")


if __name__ == '__main__':
    generate_logo()
    generate_pwa_icons()
