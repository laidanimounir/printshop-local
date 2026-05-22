import os
from datetime import datetime
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app
from database import db, Order, Worker, Transfer, Setting, generate_order_number, get_daily_stats, auto_delete_old_files
from auth import auth_bp, login_manager, worker_required, manager_required
import config

login_manager.init_app(app)
app.register_blueprint(auth_bp)


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in config.ALLOWED_EXTENSIONS


def calculate_price(copies, color_mode, paper_size, page_count=1):
    pages = copies * max(page_count, 1)
    if color_mode == 'color':
        per_page = config.PRICE_COLOR_PER_PAGE
    else:
        per_page = config.PRICE_BW_PER_PAGE
    multiplier = config.PRICE_A3_MULTIPLIER if paper_size == 'A3' else 1
    return pages * per_page * multiplier


def get_setting(key, default=None):
    s = Setting.query.filter_by(key=key).first()
    return s.value if s else default


# ====== Public Routes ======

@app.route('/')
def index():
    return redirect(url_for('upload_page', computer_id='PC1'))


@app.route('/upload/<computer_id>')
def upload_page(computer_id):
    if computer_id not in config.COMPUTERS:
        computer_id = 'PC1'
    pc = config.COMPUTERS[computer_id]
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    shop_slogan = get_setting('shop_slogan', config.SHOP_SLOGAN)
    return render_template('client.html',
                           computer_id=computer_id,
                           pc=pc,
                           shop_name=shop_name,
                           shop_slogan=shop_slogan,
                           config=config)


@app.route('/submit/<computer_id>', methods=['POST'])
def submit_order(computer_id):
    if computer_id not in config.COMPUTERS:
        return jsonify({'error': 'Invalid computer'}), 400
    if 'file' not in request.files:
        flash('Please select a file.', 'danger')
        return redirect(url_for('upload_page', computer_id=computer_id))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('upload_page', computer_id=computer_id))
    if not allowed_file(file.filename):
        flash('File type not supported.', 'danger')
        return redirect(url_for('upload_page', computer_id=computer_id))
    order_number = generate_order_number()
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    safe_name = f"{order_number}_{secure_filename(file.filename)}"
    file_path = os.path.join(config.UPLOAD_FOLDER, safe_name)
    file.save(file_path)
    copies = int(request.form.get('copies', 1))
    color_mode = request.form.get('color_mode', 'bw')
    paper_size = request.form.get('paper_size', 'A4')
    notes = request.form.get('notes', '')
    customer_phone = request.form.get('customer_phone', '')
    is_duplex = request.form.get('is_duplex') == 'on'
    from duplex_print import get_page_count
    pc = get_page_count(file_path)
    order = Order(
        order_number=order_number,
        computer_id=computer_id,
        customer_phone=customer_phone,
        file_path=file_path,
        file_name=file.filename,
        file_type=ext,
        copies=copies,
        color_mode=color_mode,
        paper_size=paper_size,
        notes=notes,
        is_duplex=is_duplex,
        duplex_status='none',
        status='new',
        price=calculate_price(copies, color_mode, paper_size, pc),
        page_count=pc
    )
    db.session.add(order)
    db.session.commit()
    return redirect(url_for('confirm_page', order_number=order_number))


@app.route('/confirm/<order_number>')
def confirm_page(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    pc = config.COMPUTERS.get(order.computer_id, {})
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('confirm.html', order=order, pc=pc, shop_name=shop_name)


# ====== Worker Routes ======

@app.route('/worker/dashboard')
@login_required
@worker_required
def worker_dashboard():
    computer_id = current_user.computer_id
    our_orders = Order.query.filter_by(
        computer_id=computer_id
    ).order_by(Order.created_at.desc()).all()
    computers = {k: v for k, v in config.COMPUTERS.items() if k != computer_id}
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('worker_dashboard.html',
                           orders=our_orders,
                           computer_id=computer_id,
                           pc=config.COMPUTERS.get(computer_id, {}),
                           computers=computers,
                           shop_name=shop_name)


@app.route('/worker/duplex/step1/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_duplex_step1(order_id):
    order = Order.query.get_or_404(order_id)
    if order.computer_id != current_user.computer_id:
        return jsonify({'error': 'Not your order'}), 403
    try:
        from duplex_print import print_duplex_step1, get_page_count
        pc = get_page_count(order.file_path)
        order.status = 'duplex_waiting'
        order.duplex_status = 'step1_done'
        order.worker_id = current_user.id
        order.updated_at = datetime.utcnow()
        db.session.commit()
        result = print_duplex_step1(order.file_path, order.copies)
        if result.get('success'):
            return jsonify({'success': True, 'message': 'Step 1 done. Flip paper and confirm.', 'total_pages': pc})
        return jsonify({'success': True, 'message': 'Step 1 sent to printer.', 'total_pages': pc})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/worker/duplex/step2/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_duplex_step2(order_id):
    order = Order.query.get_or_404(order_id)
    if order.computer_id != current_user.computer_id:
        return jsonify({'error': 'Not your order'}), 403
    try:
        from duplex_print import print_duplex_step2
        result = print_duplex_step2(order.file_path, order.copies)
        if result.get('success'):
            order.status = 'done'
            order.duplex_status = 'complete'
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Duplex printing complete'})
        return jsonify({'success': True, 'message': 'Step 2 sent to printer'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/duplex/status/<int:order_id>')
def api_duplex_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        'is_duplex': order.is_duplex,
        'duplex_status': order.duplex_status,
        'status': order.status,
        'total_pages': order.page_count
    })


@app.route('/worker/print/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_print(order_id):
    order = Order.query.get_or_404(order_id)
    if order.computer_id != current_user.computer_id:
        return jsonify({'error': 'Not your order'}), 403
    order.status = 'printing'
    order.worker_id = current_user.id
    order.updated_at = datetime.utcnow()
    db.session.commit()
    try:
        from printer import print_file
        result = print_file(order.file_path, order.copies, order.color_mode, order.paper_size)
        if result.get('success'):
            order.status = 'done'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Printed successfully'})
        return jsonify({'success': True, 'message': 'Sent to printer'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/worker/done/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_done(order_id):
    order = Order.query.get_or_404(order_id)
    if order.computer_id != current_user.computer_id:
        return jsonify({'error': 'Not your order'}), 403
    order.status = 'done'
    order.worker_id = current_user.id
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})


@app.route('/worker/transfer/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_transfer(order_id):
    order = Order.query.get_or_404(order_id)
    if order.computer_id != current_user.computer_id:
        return jsonify({'error': 'Not your order'}), 403
    data = request.get_json()
    to_computer = data.get('to_computer')
    reason = data.get('reason', '')
    if to_computer not in config.COMPUTERS:
        return jsonify({'error': 'Invalid target computer'}), 400
    transfer = Transfer(
        order_id=order.id,
        from_computer=order.computer_id,
        to_computer=to_computer,
        reason=reason
    )
    order.computer_id = to_computer
    order.status = 'transferred'
    order.updated_at = datetime.utcnow()
    db.session.add(transfer)
    db.session.commit()
    return jsonify({'success': True, 'new_computer': to_computer})


# ====== Manager Routes ======

@app.route('/manager/dashboard')
@login_required
@manager_required
def manager_dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    workers = Worker.query.filter_by(role='worker').all()
    stats = {}
    for pc_id in config.COMPUTERS:
        cnt = Order.query.filter_by(computer_id=pc_id, status='new').count()
        stats[pc_id] = {'name': config.COMPUTERS[pc_id]['name'], 'new_count': cnt}
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_dashboard.html',
                           orders=orders, workers=workers,
                           stats=stats, computers=config.COMPUTERS,
                           shop_name=shop_name)


@app.route('/manager/workers')
@login_required
@manager_required
def manager_workers():
    workers = Worker.query.all()
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_workers.html',
                           workers=workers, computers=config.COMPUTERS,
                           shop_name=shop_name)


@app.route('/manager/workers/add', methods=['POST'])
@login_required
@manager_required
def manager_workers_add():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    full_name = request.form.get('full_name', '')
    computer_id = request.form.get('computer_id', '')
    if Worker.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
    else:
        w = Worker(username=username, full_name=full_name,
                   computer_id=computer_id if computer_id else None,
                   role='worker', is_active=True)
        w.set_password(password)
        db.session.add(w)
        db.session.commit()
        flash('Worker added successfully.', 'success')
    return redirect(url_for('manager_workers'))


@app.route('/manager/workers/delete/<int:worker_id>', methods=['POST'])
@login_required
@manager_required
def manager_workers_delete(worker_id):
    w = Worker.query.get_or_404(worker_id)
    if w.role == 'manager':
        return jsonify({'error': 'Cannot delete manager'}), 400
    db.session.delete(w)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/manager/workers/edit/<int:worker_id>', methods=['POST'])
@login_required
@manager_required
def manager_workers_edit(worker_id):
    w = Worker.query.get_or_404(worker_id)
    w.full_name = request.form.get('full_name', w.full_name)
    w.computer_id = request.form.get('computer_id', w.computer_id)
    w.is_active = request.form.get('is_active') == 'on'
    password = request.form.get('password', '')
    if password:
        w.set_password(password)
    db.session.commit()
    flash('Worker updated.', 'success')
    return redirect(url_for('manager_workers'))


@app.route('/manager/reports')
@login_required
@manager_required
def manager_reports():
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_reports.html', shop_name=shop_name)


@app.route('/manager/reports/export')
@login_required
@manager_required
def manager_reports_export():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import io
    from flask import send_file
    today = datetime.utcnow().date()
    stats = get_daily_stats(today)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, f"{get_setting('shop_name', config.SHOP_NAME)} - Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Date: {today}")
    c.drawString(50, 750, f"Total Orders: {stats['orders']}")
    c.drawString(50, 730, f"Total Pages: {stats['pages']}")
    c.drawString(50, 710, f"Total Revenue: {stats['revenue']} DZD")
    c.save()
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f'report_{today}.pdf',
                     mimetype='application/pdf')


@app.route('/manager/settings', methods=['GET', 'POST'])
@login_required
@manager_required
def manager_settings():
    if request.method == 'POST':
        for key in ['shop_name', 'shop_slogan', 'price_bw', 'price_color', 'auto_delete_days']:
            val = request.form.get(key)
            if val is not None:
                s = Setting.query.filter_by(key=key).first()
                if s:
                    s.value = val
                else:
                    db.session.add(Setting(key=key, value=val))
        db.session.commit()
        flash('Settings saved.', 'success')
        return redirect(url_for('manager_settings'))
    settings = {s.key: s.value for s in Setting.query.all()}
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_settings.html', settings=settings, config=config, shop_name=shop_name)


# ====== QR Management ======

@app.route('/manager/qr')
@login_required
@manager_required
def manager_qr():
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    qr_files = {}
    for pc_id in config.COMPUTERS:
        qr_path = os.path.join(config.QR_FOLDER, f"QR_{pc_id}.png")
        qr_files[pc_id] = os.path.exists(qr_path)
    return render_template('manager_qr.html', computers=config.COMPUTERS,
                           qr_files=qr_files, shop_name=shop_name)


@app.route('/manager/qr/download/all')
@login_required
@manager_required
def manager_qr_download_all():
    from qr_generator import generate_all_qr_pdf
    pdf_path = generate_all_qr_pdf()
    return send_from_directory(config.QR_FOLDER, "all_qr_codes.pdf",
                               as_attachment=True,
                               download_name="all_qr_codes.pdf")


@app.route('/manager/qr/download/<pc_id>')
@login_required
@manager_required
def manager_qr_download(pc_id):
    if pc_id not in config.COMPUTERS:
        flash('Invalid computer', 'danger')
        return redirect(url_for('manager_qr'))
    filename = f"QR_{pc_id}_print.pdf"
    return send_from_directory(config.QR_FOLDER, filename,
                               as_attachment=True, download_name=filename)


@app.route('/manager/qr/print/all', methods=['POST'])
@login_required
@manager_required
def manager_qr_print_all():
    from qr_generator import print_qr
    results = []
    for pc_id in config.COMPUTERS:
        r = print_qr(pc_id)
        results.append({'pc': pc_id, 'success': r.get('success', False)})
    return jsonify({'results': results})


@app.route('/manager/qr/print/<pc_id>', methods=['POST'])
@login_required
@manager_required
def manager_qr_print(pc_id):
    if pc_id not in config.COMPUTERS:
        return jsonify({'error': 'Invalid'}), 400
    from qr_generator import print_qr
    result = print_qr(pc_id)
    return jsonify(result)


@app.route('/manager/qr/regenerate/<pc_id>', methods=['POST'])
@login_required
@manager_required
def manager_qr_regenerate(pc_id):
    if pc_id not in config.COMPUTERS:
        return jsonify({'error': 'Invalid'}), 400
    from qr_generator import generate_qr_for_computer
    generate_qr_for_computer(pc_id, config.COMPUTERS[pc_id])
    return jsonify({'success': True})


# ====== API Routes ======

@app.route('/api/orders/<computer_id>')
def api_orders(computer_id):
    orders = Order.query.filter_by(computer_id=computer_id)\
        .order_by(Order.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': o.id, 'order_number': o.order_number,
        'customer_phone': o.customer_phone, 'file_name': o.file_name,
        'copies': o.copies, 'color_mode': o.color_mode,
        'paper_size': o.paper_size, 'status': o.status,
        'price': o.price,
        'created_at': o.created_at.isoformat() if o.created_at else None,
        'notes': o.notes
    } for o in orders])


@app.route('/api/stats/today')
def api_stats_today():
    return jsonify(get_daily_stats())


@app.route('/api/orders/new/<computer_id>')
def api_new_orders(computer_id):
    since = request.args.get('since', '0')
    try:
        since_id = int(since)
    except ValueError:
        since_id = 0
    orders = Order.query.filter(
        Order.computer_id == computer_id,
        Order.id > since_id,
        Order.status == 'new'
    ).order_by(Order.created_at.asc()).all()
    return jsonify([{
        'id': o.id, 'order_number': o.order_number,
        'customer_phone': o.customer_phone, 'file_name': o.file_name,
        'copies': o.copies, 'color_mode': o.color_mode,
        'paper_size': o.paper_size, 'price': o.price,
        'created_at': o.created_at.isoformat() if o.created_at else None
    } for o in orders])


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(config.UPLOAD_FOLDER, filename)


# ====== Captive Portal ======
@app.route('/hotspot-detect.html')
def apple_captive():
    return redirect(url_for('upload_page', computer_id='PC1'))

@app.route('/generate_204')
def android_captive():
    return '', 204

@app.route('/ncsi.txt')
def windows_captive():
    return 'Microsoft NCSI', 200, {'Content-Type': 'text/plain'}

@app.route('/success.html')
def generic_captive():
    return redirect(url_for('upload_page', computer_id='PC1'))


# ====== Errors ======
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large(e):
    return render_template('413.html'), 413


if __name__ == '__main__':
    import sys
    if '--setup' in sys.argv:
        with app.app_context():
            from database import create_default_workers
            create_default_workers()
        print("Setup complete.")
    else:
        print(f"  {config.SHOP_NAME} - PrintShop Server")
        print(f"  Server: http://0.0.0.0:{config.SERVER_PORT}")
        print(f"  Upload: http://localhost:{config.SERVER_PORT}/upload/PC1")
        print(f"  Worker: http://localhost:{config.SERVER_PORT}/worker/login")
        print(f"  Manager: http://localhost:{config.SERVER_PORT}/manager/dashboard")
        app.run(host='0.0.0.0', port=config.SERVER_PORT, debug=True)
