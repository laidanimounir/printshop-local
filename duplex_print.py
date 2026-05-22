import os
import tempfile
from PIL import Image
import config


def get_page_count(file_path):
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    try:
        if ext == 'pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                return len(reader.pages)
            except Exception:
                pass
        elif ext in ('jpg', 'jpeg', 'png', 'bmp', 'tiff'):
            return 1
        elif ext in ('docx', 'xlsx', 'pptx'):
            return 1
    except Exception:
        pass
    return 1


def needs_blank_page(file_path):
    total = get_page_count(file_path)
    return total % 2 == 1


def split_pdf_odd_even(file_path):
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(file_path)
    total = len(reader.pages)

    odd_writer = PdfWriter()
    even_writer = PdfWriter()

    for i in range(total):
        if i % 2 == 0:
            odd_writer.add_page(reader.pages[i])
        else:
            even_writer.add_page(reader.pages[i])

    even_pages = list(range(1, total, 2))
    even_reversed = even_pages[::-1]
    even_writer2 = PdfWriter()
    for p in even_reversed:
        even_writer2.add_page(reader.pages[p])

    temp_dir = tempfile.gettempdir()
    odd_path = os.path.join(temp_dir, f"duplex_odd_{os.path.basename(file_path)}")
    even_path = os.path.join(temp_dir, f"duplex_even_{os.path.basename(file_path)}")

    odd_writer.write(odd_path)
    even_writer2.write(even_path)

    return odd_path, even_path


def print_duplex_step1(file_path, copies, printer_name=None):
    odd_path, _ = split_pdf_odd_even(file_path)
    from printer import print_file
    result = print_file(odd_path, copies, 'bw', 'A4', printer_name)
    try:
        os.remove(odd_path)
    except OSError:
        pass
    return result


def print_duplex_step2(file_path, copies, printer_name=None):
    _, even_path = split_pdf_odd_even(file_path)
    from printer import print_file
    result = print_file(even_path, copies, 'bw', 'A4', printer_name)
    try:
        os.remove(even_path)
    except OSError:
        pass
    return result


def add_blank_page_if_odd(input_path, output_path):
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    if len(reader.pages) % 2 == 1:
        writer.add_blank_page()

    writer.write(output_path)
    return output_path
