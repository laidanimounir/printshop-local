from datetime import datetime
from reportlab.lib.pagesizes import A7
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io
import os
import config


def generate_receipt_pdf(order):
    buf = io.BytesIO()
    width, height = A7
    c = canvas.Canvas(buf, pagesize=A7)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, height - 15, config.SHOP_NAME)
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, height - 25, config.SHOP_SLOGAN)
    
    c.line(10, height - 30, width - 10, height - 30)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, f"#{order.order_number}")
    
    c.setFont("Helvetica", 7)
    y = height - 65
    c.drawString(10, y, f"File: {order.file_name}")
    y -= 10
    c.drawString(10, y, f"Copies: {order.copies}")
    y -= 10
    c.drawString(10, y, f"Mode: {'Color' if order.color_mode == 'color' else 'B&W'}")
    y -= 10
    c.drawString(10, y, f"Paper: {order.paper_size}")
    y -= 10
    c.drawString(10, y, f"Phone: {order.customer_phone}")
    y -= 10
    if order.price:
        c.drawString(10, y, f"Price: {order.price} DZD")
        y -= 10
    
    c.line(10, y - 5, width - 10, y - 5)
    y -= 15
    c.setFont("Helvetica", 6)
    c.drawCentredString(width / 2, y, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
    
    c.save()
    buf.seek(0)
    return buf


def print_receipt(order, printer_name=None):
    try:
        pdf_buf = generate_receipt_pdf(order)
        temp_path = os.path.join(config.UPLOAD_FOLDER, f"receipt_{order.order_number}.pdf")
        with open(temp_path, 'wb') as f:
            f.write(pdf_buf.getvalue())
        from printer import print_file
        return print_file(temp_path, 1, 'bw', 'A4', printer_name)
    except Exception as e:
        return {'success': False, 'error': str(e)}
