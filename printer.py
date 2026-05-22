import os
import tempfile
from PIL import Image


def get_available_printers():
    try:
        import win32print
        printers = []
        for p in win32print.EnumPrinters(2):
            printers.append({
                'name': p[2],
                'description': p[3],
                'port': p[4] if len(p) > 4 else ''
            })
        return printers
    except Exception:
        return []


def get_default_printer():
    try:
        import win32print
        return win32print.GetDefaultPrinter()
    except Exception:
        return None


def print_file(file_path, copies=1, color_mode='bw', paper_size='A4', printer_name=None):
    try:
        import win32print
        import win32ui
        from PIL import ImageWin

        if not os.path.exists(file_path):
            return {'success': False, 'error': 'File not found'}

        ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''

        if printer_name is None:
            printer_name = get_default_printer()

        if not printer_name:
            return {'success': False, 'error': 'No printer available'}

        if ext in ('jpg', 'jpeg', 'png', 'bmp', 'tiff'):
            return _print_image(file_path, copies, printer_name)
        elif ext == 'pdf':
            return _print_pdf(file_path, copies, printer_name)
        elif ext in ('docx', 'xlsx', 'pptx'):
            return _print_office(file_path, copies, printer_name)
        else:
            return {'success': False, 'error': f'Cannot print .{ext} files directly'}
    except ImportError:
        return {'success': False, 'error': 'Printing not available on this system'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _print_image(file_path, copies, printer_name):
    try:
        import win32print
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            img = Image.open(file_path)
            for _ in range(copies):
                img.load()
                hdc = win32ui.CreateDC()
                hdc.CreatePrinterDC(printer_name)
                hdc.StartDoc(file_path)
                hdc.StartPage()
                dib = ImageWin.Dib(img)
                dib.draw(hdc.GetHandleOutput(), (0, 0, img.width, img.height))
                hdc.EndPage()
                hdc.EndDoc()
                hdc.DeleteDC()
        finally:
            win32print.ClosePrinter(hprinter)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _print_pdf(file_path, copies, printer_name):
    try:
        import win32print
        import win32api
        for _ in range(copies):
            win32api.ShellExecute(
                0, "print", file_path,
                f'/d:"{printer_name}"', ".", 0
            )
        return {'success': True, 'message': 'PDF sent to printer'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _print_office(file_path, copies, printer_name):
    try:
        import win32print
        import win32api
        for _ in range(copies):
            win32api.ShellExecute(
                0, "print", file_path,
                f'/d:"{printer_name}"', ".", 0
            )
        return {'success': True, 'message': 'Document sent to printer'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_printer_status(printer_name=None):
    try:
        import win32print
        if printer_name is None:
            printer_name = get_default_printer()
        if not printer_name:
            return {'available': False, 'error': 'No default printer'}
        hprinter = win32print.OpenPrinter(printer_name)
        try:
            info = win32print.GetPrinter(hprinter, 2)
            status = info.get('Status', 0)
            return {
                'available': status == 0,
                'name': printer_name,
                'status_code': status,
                'status': 'ready' if status == 0 else f'busy ({status})'
            }
        finally:
            win32print.ClosePrinter(hprinter)
    except Exception as e:
        return {'available': False, 'error': str(e)}
