import os
import shutil
import zipfile
from datetime import datetime, timedelta
import config

BACKUP_DIR = os.path.join(config.BASE_DIR, "backups")


def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def backup_database():
    ensure_backup_dir()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{ts}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if os.path.exists(config.DB_PATH):
        shutil.copy2(config.DB_PATH, backup_path)
        return {'success': True, 'path': backup_path, 'name': backup_name, 'size': os.path.getsize(backup_path)}
    return {'success': False, 'error': 'Database not found'}


def backup_uploads():
    ensure_backup_dir()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_name = f"uploads_{ts}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_name)
    if not os.path.isdir(config.UPLOAD_FOLDER):
        return {'success': False, 'error': 'Uploads folder not found'}
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(config.UPLOAD_FOLDER):
            for f in files:
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, config.BASE_DIR)
                zf.write(fp, arcname)
    return {'success': True, 'path': zip_path, 'name': zip_name, 'size': os.path.getsize(zip_path)}


def cleanup_old_backups(keep=30):
    ensure_backup_dir()
    files = []
    for f in os.listdir(BACKUP_DIR):
        fp = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(fp) and (f.startswith('backup_') or f.startswith('uploads_')):
            files.append((os.path.getmtime(fp), fp))
    files.sort()
    while len(files) > keep:
        _, fp = files.pop(0)
        try:
            os.remove(fp)
        except OSError:
            pass


def get_backup_list():
    ensure_backup_dir()
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        fp = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(fp) and (f.startswith('backup_') or f.startswith('uploads_')):
            backups.append({
                'name': f,
                'size': os.path.getsize(fp),
                'date': datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M"),
                'type': 'database' if f.startswith('backup_') else 'uploads'
            })
    return backups


def run_full_backup():
    result = {'database': None, 'uploads': None}
    result['database'] = backup_database()
    result['uploads'] = backup_uploads()
    cleanup_old_backups(30)
    return result


def check_backup_needed():
    ensure_backup_dir()
    now = datetime.utcnow()
    for f in os.listdir(BACKUP_DIR):
        if f.startswith('backup_'):
            fp = os.path.join(BACKUP_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if now - mtime < timedelta(hours=24):
                return False
    return True
