import re
import os
from functools import wraps
from datetime import datetime, timedelta
from flask import request, abort, session
from werkzeug.utils import secure_filename
import config

request_counts = {}

def rate_limit(max_requests=10, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr or 'unknown'
            now = datetime.utcnow()
            key = f"{ip}:{f.__name__}"
            if key not in request_counts:
                request_counts[key] = []
            request_counts[key] = [
                t for t in request_counts[key]
                if now - t < timedelta(seconds=window_seconds)
            ]
            if len(request_counts[key]) >= max_requests:
                abort(429)
            request_counts[key].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def sanitize_filename(filename):
    name = secure_filename(filename)
    name = re.sub(r'[^\w\.\-]', '_', name)
    return name


def validate_file_extension(filename):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in config.ALLOWED_EXTENSIONS


def validate_file_content(file_path):
    ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
    try:
        if ext in ('jpg', 'jpeg', 'png', 'bmp', 'gif'):
            from PIL import Image
            img = Image.open(file_path)
            img.verify()
        elif ext == 'pdf':
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return False
        elif ext in ('docx', 'xlsx', 'pptx'):
            import zipfile
            if not zipfile.is_zipfile(file_path):
                return False
        return True
    except Exception:
        return False


def sanitize_phone(phone):
    cleaned = re.sub(r'[^\d+]', '', phone)
    if len(cleaned) < 8:
        return None
    return cleaned


def validate_order_input(data):
    errors = []
    if not data.get('customer_phone'):
        errors.append('Phone number is required')
    copies = data.get('copies', 1)
    try:
        copies = int(copies)
        if copies < 1 or copies > 100:
            errors.append('Copies must be between 1 and 100')
    except (ValueError, TypeError):
        errors.append('Invalid copies value')
    color_mode = data.get('color_mode', 'bw')
    if color_mode not in ('bw', 'color'):
        errors.append('Invalid color mode')
    paper_size = data.get('paper_size', 'A4')
    if paper_size not in ('A4', 'A3'):
        errors.append('Invalid paper size')
    return errors
