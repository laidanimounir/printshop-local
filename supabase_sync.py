import json
from datetime import datetime
from database import Order
import config

SUPABASE_ENABLED = config.SUPABASE_ENABLED
SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_KEY


def sync_order_to_cloud(order):
    if not SUPABASE_ENABLED:
        return
    try:
        import requests
        data = {
            'order_number': order.order_number,
            'computer_id': order.computer_id,
            'customer_phone': order.customer_phone,
            'file_name': order.file_name,
            'copies': order.copies,
            'color_mode': order.color_mode,
            'paper_size': order.paper_size,
            'status': order.status,
            'price': order.price,
            'created_at': order.created_at.isoformat() if order.created_at else None
        }
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        requests.post(
            f'{SUPABASE_URL}/rest/v1/orders',
            json=data,
            headers=headers,
            timeout=10
        )
    except Exception as e:
        print(f"Supabase sync error: {e}")


def sync_worker_stats(worker_id, stats):
    if not SUPABASE_ENABLED:
        return
    try:
        import requests
        data = {
            'worker_id': worker_id,
            'date': datetime.utcnow().date().isoformat(),
            'orders_count': stats.get('orders', 0),
            'pages_count': stats.get('pages', 0),
            'revenue': stats.get('revenue', 0)
        }
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }
        requests.post(
            f'{SUPABASE_URL}/rest/v1/worker_stats',
            json=data,
            headers=headers,
            timeout=10
        )
    except Exception as e:
        print(f"Supabase stats sync error: {e}")


def pull_remote_settings():
    if not SUPABASE_ENABLED:
        return {}
    try:
        import requests
        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
        resp = requests.get(
            f'{SUPABASE_URL}/rest/v1/settings',
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            settings = {}
            for item in resp.json():
                settings[item['key']] = item['value']
            return settings
    except Exception as e:
        print(f"Supabase settings pull error: {e}")
    return {}


def backup_database():
    if not SUPABASE_ENABLED:
        return
    try:
        import requests
        db_path = config.DB_PATH
        if not os.path.exists(db_path):
            return
        import os
        with open(db_path, 'rb') as f:
            files = {'file': ('printshop_backup.db', f, 'application/octet-stream')}
            headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}'
            }
            requests.post(
                f'{SUPABASE_URL}/storage/v1/object/backups/printshop.db',
                files=files,
                headers=headers,
                timeout=30
            )
    except Exception as e:
        print(f"Supabase backup error: {e}")
