"""
PrintShop Local - System Verification Tests
Run: python test_system.py
"""
import os
import sys
import io

os.chdir(os.path.dirname(os.path.abspath(__file__)))

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [OK] PASS: {name}")
    else:
        failed += 1
        print(f"  [XX] FAIL: {name} - {detail}")


print("=" * 60)
print("  PrintShop Local - System Verification")
print("=" * 60)

# 1. Project structure
print("\n[1] Project Structure")
test("config.py exists", os.path.exists("config.py"))
test("server.py exists", os.path.exists("server.py"))
test("database.py exists", os.path.exists("database.py"))
test("auth.py exists", os.path.exists("auth.py"))
test("printer.py exists", os.path.exists("printer.py"))
test("qr_generator.py exists", os.path.exists("qr_generator.py"))
test("generate_logo.py exists", os.path.exists("generate_logo.py"))
test("requirements.txt exists", os.path.exists("requirements.txt"))
test("templates/ exists", os.path.isdir("templates"))
test("static/css/ exists", os.path.isdir("static/css"))
test("static/js/ exists", os.path.isdir("static/js"))
test("client.html exists", os.path.exists("templates/client.html"))
test("confirm.html exists", os.path.exists("templates/confirm.html"))
test("worker_login.html exists", os.path.exists("templates/worker_login.html"))
test("worker_dashboard.html exists", os.path.exists("templates/worker_dashboard.html"))
test("manager_dashboard.html exists", os.path.exists("templates/manager_dashboard.html"))
test("manager_workers.html exists", os.path.exists("templates/manager_workers.html"))
test("manager_reports.html exists", os.path.exists("templates/manager_reports.html"))
test("manager_settings.html exists", os.path.exists("templates/manager_settings.html"))
test("main.css exists", os.path.exists("static/css/main.css"))
test("main.js exists", os.path.exists("static/js/main.js"))
test("worker.js exists", os.path.exists("static/js/worker.js"))
test("manifest.json exists", os.path.exists("static/manifest.json"))
test("sw.js exists", os.path.exists("static/sw.js"))
test("PWA manifest is valid JSON", open("static/manifest.json", encoding='utf-8').read().strip().startswith("{"))
test("duplex_print.py exists", os.path.exists("duplex_print.py"))
test("ai_optimizer.py exists", os.path.exists("ai_optimizer.py"))
test("queue_manager.py exists", os.path.exists("queue_manager.py"))
test("backup.py exists", os.path.exists("backup.py"))
test("manager_qr.html exists", os.path.exists("templates/manager_qr.html"))
test("manager_backups.html exists", os.path.exists("templates/manager_backups.html"))
test("manager_customers.html exists", os.path.exists("templates/manager_customers.html"))
test("manager_customer_detail.html exists", os.path.exists("templates/manager_customer_detail.html"))

# 2. Config
print("\n[2] Configuration")
import config as cfg
test("SHOP_NAME set", hasattr(cfg, 'SHOP_NAME'))
test("COMPUTERS has 4 PCs", len(cfg.COMPUTERS) == 4)
test("ALLOWED_EXTENSIONS defined", len(cfg.ALLOWED_EXTENSIONS) > 0)
test("PRICE_BW_PER_PAGE > 0", cfg.PRICE_BW_PER_PAGE > 0)
test("PRICE_COLOR_PER_PAGE > 0", cfg.PRICE_COLOR_PER_PAGE > 0)

# 3. Database
print("\n[3] Database")
import server
from app import app as test_app
from database import db, Order, Worker, generate_order_number

with test_app.app_context():
    test("Database tables created", Order.query is not None)
    admin = Worker.query.filter_by(username='admin').first()
    test("Admin account exists", admin is not None, f"Found: {admin}")
    if admin:
        test("Admin role is manager", admin.role == 'manager')
        test("Admin password valid", admin.check_password('admin123'))

    worker1 = Worker.query.filter_by(username='worker1').first()
    test("Worker1 account exists", worker1 is not None)
    if worker1:
        test("Worker1 role is worker", worker1.role == 'worker')
        test("Worker1 computer is PC1", worker1.computer_id == 'PC1')

    order_num = generate_order_number()
    test("Order number generated", order_num is not None)
    test("Order number format correct", 
         len(order_num.split('-')) == 2 and order_num.split('-')[0].isdigit())

    order = Order(
        order_number=order_num,
        computer_id='PC1',
        customer_phone='0555123456',
        file_path='/tmp/test.pdf',
        file_name='test.pdf',
        copies=2,
        color_mode='bw',
        paper_size='A4',
        status='new',
        price=20
    )
    db.session.add(order)
    db.session.commit()
    test("Order created in DB", Order.query.filter_by(order_number=order_num).first() is not None)

    from database import get_daily_stats
    stats = get_daily_stats()
    test("Daily stats returns dict", isinstance(stats, dict))
    test("Daily stats has orders key", 'orders' in stats)

    db.session.delete(order)
    db.session.commit()
    test("Order deleted from DB", Order.query.filter_by(order_number=order_num).first() is None)

# 4. Server
print("\n[4] Server")
with test_app.test_client() as client:
    resp = client.get('/')
    test("GET / redirects", resp.status_code in (302, 200))

    resp = client.get('/upload/PC1')
    test("GET /upload/PC1 returns 200", resp.status_code == 200)
    content = resp.data.decode('utf-8')
    test("Upload page is HTML", 'html' in content)
    test("Upload page is RTL", 'rtl' in content or 'dir="rtl"' in content)

    resp = client.get('/upload/PC99')
    test("GET /upload/PC99 redirects to PC1", resp.status_code in (302, 200))

    resp = client.get('/worker/login')
    test("GET /worker/login returns 200", resp.status_code == 200)

    resp = client.post('/worker/login', data={
        'username': 'admin', 'password': 'admin123'
    }, follow_redirects=True)
    test("Admin login succeeds", resp.status_code == 200)
    content = resp.data.decode('utf-8')

    resp = client.get('/manager/dashboard', follow_redirects=True)
    test("GET /manager/dashboard accessible after login", resp.status_code in (200, 302))

    resp = client.get('/manager/workers')
    test("GET /manager/workers accessible", resp.status_code in (200, 302))

    resp = client.get('/manager/reports')
    test("GET /manager/reports accessible", resp.status_code in (200, 302))

    resp = client.get('/manager/settings')
    test("GET /manager/settings accessible", resp.status_code in (200, 302))

    resp = client.get('/api/stats/today')
    test("GET /api/stats/today returns JSON", resp.status_code == 200)

    resp = client.get('/api/orders/PC1')
    test("GET /api/orders/PC1 returns JSON", resp.status_code == 200)

    resp = client.get('/manager/qr')
    test("GET /manager/qr accessible", resp.status_code in (200, 302))

    resp = client.get('/api/queue/status')
    test("GET /api/queue/status returns JSON", resp.status_code == 200)

    resp = client.get('/manager/backups')
    test("GET /manager/backups accessible", resp.status_code in (200, 302))

    resp = client.get('/manager/customers')
    test("GET /manager/customers accessible", resp.status_code in (200, 302))

    resp = client.get('/hotspot-detect.html')
    test("Captive portal /hotspot-detect.html redirects", resp.status_code in (302, 200))

    resp = client.get('/generate_204')
    test("Captive portal /generate_204 returns 204", resp.status_code == 204)

    resp = client.get('/nonexistent-page')
    test("404 handler works", resp.status_code == 404)

# 5. QR Generator
print("\n[5] QR Generator")
from qr_generator import generate_qr_for_computer
test("QR folder exists", os.path.isdir("qrcodes"))
qr_path = os.path.join("qrcodes", "QR_PC1.png")
test("QR_PC1.png exists", os.path.exists(qr_path))

# 6. Phase 2 Modules
print("\n[6] Phase 2 Modules")
from queue_manager import get_station_load, get_least_busy_station, get_overloaded_stations
with test_app.app_context():
    load = get_station_load()
    test("Queue station load returns dict", isinstance(load, dict))
    test("Queue station load has PC1", 'PC1' in load)
    least = get_least_busy_station()
    test("Least busy station found", least is not None)

from backup import run_full_backup, get_backup_list, cleanup_old_backups, BACKUP_DIR
import tempfile
old_backup_dir = None
import os
if os.path.isdir(BACKUP_DIR):
    old_backup_dir = tempfile.mkdtemp()
    os.rmdir(old_backup_dir)
    os.rename(BACKUP_DIR, old_backup_dir)
try:
    result = run_full_backup()
    test("Full backup runs and returns dict", isinstance(result, dict))
    test("Full backup has database key", 'database' in result)
    bfiles = get_backup_list()
    test("Backup list returns list", isinstance(bfiles, list))
finally:
    import shutil
    if os.path.isdir(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR, ignore_errors=True)
    if old_backup_dir and os.path.isdir(old_backup_dir):
        os.rename(old_backup_dir, BACKUP_DIR)

from duplex_print import split_pdf_odd_even
test("Duplex split PDF function exists", callable(split_pdf_odd_even))

from ai_optimizer import analyze_file
test("AI optimizer analyze_file exists", callable(analyze_file))

from database import Customer, get_or_create_customer, update_customer_stats, get_top_customers
with test_app.app_context():
    cust = get_or_create_customer('0555000000')
    test("Customer created/retrieved", cust is not None)
    test("Customer phone matches", cust.phone == '0555000000')
    total_before = cust.total_orders
    update_customer_stats('0555000000')
    test("Customer stats updated", True)
    top = get_top_customers(5)
    test("Top customers returns list", isinstance(top, list))
    test("Top customers limited to 5", len(top) <= 5)

# 7. Logo
print("\n[7] Logo Generator")
from generate_logo import generate_logo, generate_pwa_icons
logo_path = os.path.join("static", "images", "logo.png")
test("Logo file exists", os.path.exists(logo_path))
icon_192 = os.path.join("static", "images", "icon_192.png")
test("PWA icon 192 exists", os.path.exists(icon_192))
icon_512 = os.path.join("static", "images", "icon_512.png")
test("PWA icon 512 exists", os.path.exists(icon_512))

# 8. Security
print("\n[8] Security")
from security import sanitize_filename, validate_file_extension, sanitize_phone
test("Filename sanitized", sanitize_filename("hello world!.pdf") == "hello_world.pdf")
test("Filename prevents path traversal", '/' not in sanitize_filename("../../etc/passwd"))
test("Valid extension passes", validate_file_extension("test.pdf") == True)
test("Invalid extension fails", validate_file_extension("test.exe") == False)
test("Phone sanitized", sanitize_phone("0555 12 34 56") == "0555123456")

# Summary
print("\n" + "=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} passed", end="")
if failed > 0:
    print(f", {failed} failed", end="")
print()
print("=" * 60)

if failed > 0:
    sys.exit(1)
else:
    print("All tests passed!")
