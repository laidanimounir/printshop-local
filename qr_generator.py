import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageDraw, ImageFont
import config


def generate_qr_for_computer(computer_id, pc_info):
    qr_data = (
        f"WIFI:T:WPA;S:{config.WIFI_SSID};"
        f"P:{config.WIFI_PASSWORD};H:false;;\n"
        f"http://{pc_info['ip']}:{config.SERVER_PORT}/upload/{computer_id}"
    )

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color=config.COLOR_DARK,
        back_color=config.COLOR_LIGHT
    ).convert('RGB')

    qr_w, qr_h = qr_img.size
    padding = 60
    label_height = 100
    canvas_w = qr_w + padding * 2
    canvas_h = qr_h + padding * 2 + label_height
    canvas = Image.new('RGB', (canvas_w, canvas_h), config.COLOR_LIGHT)
    draw = ImageDraw.Draw(canvas)

    canvas.paste(qr_img, (padding, padding))

    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    try:
        logo_path = os.path.join(config.BASE_DIR, "static", "images", "logo.png")
        if os.path.exists(logo_path):
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = 80
            logo = logo.resize((logo_size, logo_size))
            logo_x = (canvas_w - logo_size) // 2
            logo_y = (canvas_h - label_height - logo_size) // 2
            canvas.paste(logo, (logo_x, logo_y), logo)
    except Exception:
        pass

    label1 = f"{config.SHOP_NAME} — {computer_id}"
    bbox1 = draw.textbbox((0, 0), label1, font=font_large)
    tx1 = (canvas_w - (bbox1[2] - bbox1[0])) // 2
    ty1 = qr_h + padding * 2 + 5
    draw.text((tx1, ty1), label1, fill=config.COLOR_PRIMARY, font=font_large)

    label2 = pc_info['name']
    bbox2 = draw.textbbox((0, 0), label2, font=font_small)
    tx2 = (canvas_w - (bbox2[2] - bbox2[0])) // 2
    ty2 = ty1 + 35
    draw.text((tx2, ty2), label2, fill=config.COLOR_SECONDARY, font=font_small)

    os.makedirs(config.QR_FOLDER, exist_ok=True)
    qr_path = os.path.join(config.QR_FOLDER, f"QR_{computer_id}.png")
    canvas.save(qr_path)

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdf_canvas

    pdf_path = os.path.join(config.QR_FOLDER, f"QR_{computer_id}_print.pdf")
    c = pdf_canvas.Canvas(pdf_path, pagesize=A4)
    a4_w, a4_h = A4
    margin = 50
    max_w = a4_w - 2 * margin
    max_h = a4_h - 2 * margin
    img_w, img_h = canvas.size
    scale = min(max_w / img_w, max_h / img_h)
    display_w = img_w * scale
    display_h = img_h * scale
    dx = (a4_w - display_w) / 2
    dy = (a4_h - display_h) / 2
    c.drawImage(qr_path, dx, dy, width=display_w, height=display_h)
    c.save()

    print(f"  QR Code saved: {qr_path}")
    print(f"  PDF saved: {pdf_path}")
    return qr_path, pdf_path


def generate_all_qr_codes():
    print("Generating QR Codes...")
    for pc_id, pc_info in config.COMPUTERS.items():
        generate_qr_for_computer(pc_id, pc_info)
    print("All QR Codes generated successfully!")


if __name__ == '__main__':
    generate_all_qr_codes()
