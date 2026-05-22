import os
from werkzeug.utils import secure_filename
from PIL import Image
import config


def validate_file(filename, content_length):
    if not filename or '.' not in filename:
        return False, 'Invalid filename'
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return False, f'File type .{ext} is not supported'
    max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024
    if content_length > max_bytes:
        return False, f'File exceeds {config.MAX_FILE_SIZE_MB}MB limit'
    return True, None


def save_upload(file, order_number, index=0):
    original_name = secure_filename(file.filename)
    safe_name = f"{order_number}_{index}_{original_name}"
    file_path = os.path.join(config.UPLOAD_FOLDER, safe_name)
    file.save(file_path)
    return file_path, original_name


def get_file_info(file_path):
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    page_count = 1
    thumbnail_path = None
    try:
        if ext in ('jpg', 'jpeg', 'png'):
            img = Image.open(file_path)
            page_count = 1
            thumb = img.copy()
            thumb.thumbnail((400, 400))
            thumb_dir = os.path.join(config.UPLOAD_FOLDER, 'thumbs')
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_name = f"thumb_{os.path.basename(file_path)}"
            thumb_path = os.path.join(thumb_dir, thumb_name)
            thumb.save(thumb_path)
            thumbnail_path = f"uploads/thumbs/{thumb_name}"
        elif ext == 'pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                page_count = len(reader.pages)
            except Exception:
                page_count = 1
    except Exception:
        page_count = 1
    size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    return {
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'file_type': ext,
        'page_count': page_count,
        'size_bytes': size_bytes,
        'thumbnail_path': thumbnail_path
    }


def process_multiple_files(files, order_number):
    results = []
    for idx, file in enumerate(files):
        file_path, original_name = save_upload(file, order_number, idx)
        info = get_file_info(file_path)
        info['original_name'] = original_name
        results.append(info)
    return results
