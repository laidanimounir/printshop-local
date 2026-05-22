import os
import tempfile
from PIL import Image
import config


def get_page_count(file_path):
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    try:
        if ext == 'pdf':
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return len(reader.pages)
        elif ext in ('jpg', 'jpeg', 'png'):
            return 1
        elif ext in ('docx', 'xlsx', 'pptx'):
            return 1
    except Exception:
        pass
    return 1


def analyze_file(file_path):
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    result = {
        'rotated_pages': [],
        'blank_pages': [],
        'has_meaningful_color': True,
        'ink_coverage_percent': 0,
        'total_pages': 0,
        'suggestions': [],
        'auto_fixes_available': []
    }

    if ext == 'pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            result['total_pages'] = len(reader.pages)
            for i, page in enumerate(reader.pages):
                pn = i + 1
                box = page.mediabox
                if box.width > box.height:
                    result['rotated_pages'].append(pn)
                text = page.extract_text() or ''
                if not text.strip():
                    result['blank_pages'].append(pn)

            if result['rotated_pages']:
                pages_str = ', '.join(str(p) for p in result['rotated_pages'][:5])
                result['suggestions'].append(
                    f"صفحة {pages_str} محتاجة تدوير"
                )
                result['auto_fixes_available'].append('rotate')

            if result['blank_pages']:
                pages_str = ', '.join(str(p) for p in result['blank_pages'][:5])
                result['suggestions'].append(
                    f"صفحة {pages_str} فارغة — يمكن حذفها"
                )
                result['auto_fixes_available'].append('remove_blanks')

            total_pixels = 0
            gray_pixels = 0
            for page in reader.pages.pages[:3]:
                try:
                    for img in page.images:
                        pil_img = img.to_pil()
                        if pil_img.mode == 'RGB':
                            pixels = list(pil_img.getdata())
                            total_pixels += len(pixels)
                            for r, g, b in pixels:
                                if abs(r - g) < 20 and abs(g - b) < 20:
                                    gray_pixels += 1
                except Exception:
                    pass

            if total_pixels > 0:
                gray_ratio = gray_pixels / total_pixels
                result['ink_coverage_percent'] = (1 - gray_ratio) * 100
                if gray_ratio > 0.95:
                    result['has_meaningful_color'] = False
                    result['suggestions'].append(
                        "الملف بدون ألوان مهمة — طباعة أبيض/أسود يوفر الحبر"
                    )

        except Exception:
            pass

    elif ext in ('jpg', 'jpeg', 'png'):
        result['total_pages'] = 1
        try:
            img = Image.open(file_path)
            if img.width > img.height:
                result['rotated_pages'].append(1)
                result['suggestions'].append("الصورة محتاجة تدوير")
                result['auto_fixes_available'].append('rotate')
            pixels = list(img.convert('RGB').getdata())
            total = len(pixels)
            gray = sum(1 for r, g, b in pixels if abs(r - g) < 20 and abs(g - b) < 20)
            if total > 0 and gray / total > 0.95:
                result['has_meaningful_color'] = False
                result['suggestions'].append("صورة أبيض وأسود — استخدم طباعة B&W لتوفير الحبر")
        except Exception:
            pass
    else:
        result['total_pages'] = 1

    return result


def auto_fix_pdf(file_path, fixes=None):
    if fixes is None:
        fixes = []
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(file_path)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        skip = False
        if 'remove_blanks' in fixes:
            text = page.extract_text() or ''
            if not text.strip():
                skip = True
        if not skip:
            if 'rotate' in fixes:
                box = page.mediabox
                if box.width > box.height:
                    page.rotate(90)
            writer.add_page(page)

    temp_dir = tempfile.gettempdir()
    out_path = os.path.join(temp_dir, f"optimized_{os.path.basename(file_path)}")
    writer.write(out_path)
    return out_path
