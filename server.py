import os
from datetime import datetime
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app
from database import db, Order, OrderFile, Worker, Transfer, Setting, generate_order_number, get_daily_stats, auto_delete_old_files
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
    files = request.files.getlist('files')
    if not files or len(files) == 0 or (len(files) == 1 and files[0].filename == ''):
        flash('Please select at least one file.', 'danger')
        return redirect(url_for('upload_page', computer_id=computer_id))
    if len(files) > 10:
        flash('Maximum 10 files per order.', 'danger')
        return redirect(url_for('upload_page', computer_id=computer_id))
    for f in files:
        if f.filename and not allowed_file(f.filename):
            flash(f'File type not supported: {f.filename}', 'danger')
            return redirect(url_for('upload_page', computer_id=computer_id))
    order_number = generate_order_number()
    copies = int(request.form.get('copies', 1))
    color_mode = request.form.get('color_mode', 'bw')
    paper_size = request.form.get('paper_size', 'A4')
    notes = request.form.get('notes', '')
    customer_phone = request.form.get('customer_phone', '')
    is_duplex = request.form.get('is_duplex') == 'on'
    from file_handler import process_multiple_files, get_file_info
    file_results = process_multiple_files(files, order_number)
    total_pages = sum(r.get('page_count', 1) for r in file_results)
    total_price = calculate_price(copies, color_mode, paper_size, total_pages)
    from ai_optimizer import analyze_file
    first_file = file_results[0]['file_path']
    ai_result = analyze_file(first_file)
    ai_suggestions = '|'.join(ai_result.get('suggestions', [])) if ai_result.get('suggestions') else ''
    order = Order(
        order_number=order_number,
        computer_id=computer_id,
        customer_phone=customer_phone,
        file_path=file_results[0]['file_path'],
        file_name=', '.join(r['original_name'] for r in file_results),
        file_type='multi',
        copies=copies,
        color_mode=color_mode,
        paper_size=paper_size,
        notes=f"{len(file_results)} files - {notes}" if notes else f"{len(file_results)} files",
        is_duplex=is_duplex,
        duplex_status='none',
        status='new',
        price=total_price,
        page_count=total_pages,
        ai_suggestions=ai_suggestions
    )
    db.session.add(order)
    db.session.commit()
    for r in file_results:
        of = OrderFile(
            order_id=order.id,
            file_path=r['file_path'],
            file_name=r['original_name'],
            file_type=r['file_type'],
            page_count=r.get('page_count', 1),
            thumbnail_path=r.get('thumbnail_path'),
            print_status='pending',
            sort_order=0
        )
        db.session.add(of)
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


@app.route('/worker/optimize/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_optimize(order_id):
    order = Order.query.get_or_404(order_id)
    
    data = request.get_json()
    fixes = data.get('fixes', [])
    from ai_optimizer import auto_fix_pdf, analyze_file
    try:
        fixed_path = auto_fix_pdf(order.file_path, fixes)
        order.file_path = fixed_path
        order.ai_suggestions = ''
        order.updated_at = datetime.utcnow()
        db.session.commit()
        new_analysis = analyze_file(fixed_path)
        return jsonify({'success': True, 'message': 'تم تحسين الملف', 'analysis': new_analysis})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/worker/print/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_print(order_id):
    order = Order.query.get_or_404(order_id)
    
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


@app.route('/worker/payment/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_payment(order_id):
    order = Order.query.get_or_404(order_id)
    
    data = request.get_json()
    amount_received = float(data.get('amount_received', 0))
    payment_method = data.get('payment_method', 'cash')
    order.payment_status = 'paid'
    order.payment_method = payment_method
    order.amount_received = amount_received
    order.change_given = max(0, amount_received - (order.price or 0))
    order.status = 'done'
    order.worker_id = current_user.id
    order.updated_at = datetime.utcnow()
    db.session.commit()
    from database import get_or_create_customer, update_customer_stats
    cust = get_or_create_customer(order.customer_phone)
    update_customer_stats(order.customer_phone)
    return jsonify({'success': True, 'change': order.change_given})


@app.route('/worker/done/<int:order_id>', methods=['POST'])
@login_required
@worker_required
def worker_done(order_id):
    order = Order.query.get_or_404(order_id)
    
    order.payment_status = 'unpaid'
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
    is_json = request.is_json
    source = request.get_json() if is_json else request.form
    w.full_name = source.get('full_name', w.full_name)
    w.computer_id = source.get('computer_id', w.computer_id)
    w.is_active = source.get('is_active', 'on') == 'on' or source.get('is_active') == True
    password = source.get('password', '')
    if password:
        w.set_password(password)
    db.session.commit()
    if is_json:
        return jsonify({'success': True, 'message': 'Worker updated'})
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


@app.route('/manager/customers')
@login_required
@manager_required
def manager_customers():
    from database import Customer, get_top_customers
    customers = Customer.query.order_by(Customer.last_visit.desc()).all()
    top = get_top_customers(10)
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_customers.html', customers=customers,
                           top=top, shop_name=shop_name)


@app.route('/manager/customers/<phone>')
@login_required
@manager_required
def manager_customer_detail(phone):
    from database import Customer
    customer = Customer.query.filter_by(phone=phone).first_or_404()
    orders = Order.query.filter_by(customer_phone=phone).order_by(Order.created_at.desc()).all()
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_customer_detail.html',
                           customer=customer, orders=orders, shop_name=shop_name)


@app.route('/manager/customers/discount', methods=['POST'])
@login_required
@manager_required
def manager_customer_discount():
    from database import Customer
    phone = request.form.get('phone')
    discount = int(request.form.get('discount', 0))
    customer = Customer.query.filter_by(phone=phone).first()
    if customer:
        customer.discount_percent = discount
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404


@app.route('/manager/customers/vip', methods=['POST'])
@login_required
@manager_required
def manager_customer_vip():
    from database import Customer
    data = request.get_json()
    customer = Customer.query.filter_by(phone=data.get('phone')).first()
    if customer:
        customer.is_vip = not customer.is_vip
        db.session.commit()
        return jsonify({'success': True, 'is_vip': customer.is_vip})
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/customer/<phone>')
def api_customer(phone):
    from database import Customer
    customer = Customer.query.filter_by(phone=phone).first()
    if customer:
        return jsonify({
            'phone': customer.phone,
            'name': customer.name,
            'total_orders': customer.total_orders,
            'total_spent': customer.total_spent,
            'discount_percent': customer.discount_percent,
            'is_vip': customer.is_vip
        })
    return jsonify({'exists': False})


@app.route('/manager/settings', methods=['GET', 'POST'])
@login_required
@manager_required
def manager_settings():
    if request.method == 'POST':
        is_json = request.is_json
        source = request.get_json() if is_json else request.form
        for key in ['shop_name', 'shop_slogan', 'price_bw', 'price_color', 'auto_delete_days']:
            val = source.get(key)
            if val is not None:
                s = Setting.query.filter_by(key=key).first()
                if s:
                    s.value = val
                else:
                    db.session.add(Setting(key=key, value=val))
        db.session.commit()
        if is_json:
            return jsonify({'success': True, 'message': 'Settings saved'})
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


# ====== Queue Management ======

@app.route('/api/queue/status')
def api_queue_status():
    from queue_manager import get_station_load, get_overloaded_stations
    loads = get_station_load()
    overloaded = get_overloaded_stations(5)
    least = None
    if overloaded:
        from queue_manager import get_least_busy_station
        least = get_least_busy_station()
    result = {}
    for pc_id in config.COMPUTERS:
        result[pc_id] = {
            'name': config.COMPUTERS[pc_id]['name'],
            'load': loads.get(pc_id, 0),
            'overloaded': pc_id in overloaded
        }
    return jsonify({'stations': result, 'least_busy': least})


@app.route('/api/queue/redirect/<int:order_id>/<target_pc>', methods=['POST'])
@login_required
@worker_required
def api_queue_redirect(order_id, target_pc):
    if target_pc not in config.COMPUTERS:
        return jsonify({'error': 'Invalid target'}), 400
    order = Order.query.get_or_404(order_id)
    
    transfer = Transfer(
        order_id=order.id,
        from_computer=order.computer_id,
        to_computer=target_pc,
        reason='Auto-balance'
    )
    order.computer_id = target_pc
    order.status = 'transferred'
    order.updated_at = datetime.utcnow()
    db.session.add(transfer)
    db.session.commit()
    return jsonify({'success': True, 'new_computer': target_pc})


# ====== API Routes ======

@app.route('/api/orders/all')
@login_required
def api_orders_all():
    if current_user.role != 'manager':
        return jsonify({'error': 'unauthorized'}), 401
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([{
        'id': o.id, 'order_number': o.order_number,
        'customer_phone': o.customer_phone, 'file_name': o.file_name,
        'copies': o.copies, 'color_mode': o.color_mode,
        'paper_size': o.paper_size, 'status': o.status,
        'price': o.price, 'payment_status': o.payment_status,
        'payment_method': o.payment_method,
        'amount_received': o.amount_received,
        'page_count': o.page_count, 'is_duplex': o.is_duplex,
        'duplex_status': o.duplex_status, 'computer_id': o.computer_id,
        'worker_id': o.worker_id, 'notes': o.notes,
        'created_at': o.created_at.isoformat() if o.created_at else None,
        'updated_at': o.updated_at.isoformat() if o.updated_at else None
    } for o in orders])


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


@app.route('/api/reports')
def api_reports():
    if not current_user.is_authenticated or current_user.role != 'manager':
        return jsonify({'error': 'unauthorized'}), 401
    from datetime import date, timedelta
    range_val = request.args.get('range', 'today')
    today = date.today()
    if range_val == 'week':
        start = today - timedelta(days=7)
    elif range_val == 'month':
        start = today - timedelta(days=30)
    else:
        start = today
    stats = get_daily_stats(today)
    return jsonify({
        'range': range_val,
        'orders': stats.get('orders', 0),
        'pages': stats.get('pages', 0),
        'revenue': stats.get('revenue', 0),
    })


@app.route('/api/workers')
def api_workers():
    if not current_user.is_authenticated or current_user.role != 'manager':
        return jsonify({'error': 'unauthorized'}), 401
    workers = Worker.query.all()
    return jsonify([{
        'id': w.id, 'username': w.username, 'full_name': w.full_name,
        'role': w.role, 'computer_id': w.computer_id or '',
        'is_active': w.is_active
    } for w in workers])


@app.route('/api/customers')
def api_customers():
    if not current_user.is_authenticated or current_user.role != 'manager':
        return jsonify({'error': 'unauthorized'}), 401
    from database import Customer
    customers = Customer.query.order_by(Customer.last_visit.desc()).all()
    return jsonify([{
        'phone': c.phone, 'name': c.name,
        'total_orders': c.total_orders, 'total_spent': c.total_spent,
        'discount_percent': c.discount_percent, 'is_vip': c.is_vip,
        'last_visit': c.last_visit.isoformat() if c.last_visit else None
    } for c in customers])


@app.route('/api/customers/<phone>')
def api_customers_detail(phone):
    if not current_user.is_authenticated or current_user.role != 'manager':
        return jsonify({'error': 'unauthorized'}), 401
    from database import Customer
    customer = Customer.query.filter_by(phone=phone).first()
    if not customer:
        return jsonify({'error': 'not found'}), 404
    orders = Order.query.filter_by(customer_phone=phone)\
        .order_by(Order.created_at.desc()).all()
    return jsonify({
        'phone': customer.phone, 'name': customer.name,
        'total_orders': customer.total_orders, 'total_spent': customer.total_spent,
        'discount_percent': customer.discount_percent, 'is_vip': customer.is_vip,
        'last_visit': customer.last_visit.isoformat() if customer.last_visit else None,
        'orders': [{
            'id': o.id, 'order_number': o.order_number,
            'status': o.status, 'price': o.price,
            'payment_status': o.payment_status,
            'created_at': o.created_at.isoformat() if o.created_at else None
        } for o in orders]
    })


@app.route('/api/backups')
def api_backups():
    if not current_user.is_authenticated or current_user.role != 'manager':
        return jsonify({'error': 'unauthorized'}), 401
    from backup import get_backup_list
    backups = get_backup_list()
    return jsonify([{
        'filename': b['name'],
        'size': str(b['size']),
        'created_at': b['date'],
        'type': b['type']
    } for b in backups])


@app.route('/api/me')
def api_me():
    if not current_user.is_authenticated:
        return jsonify({'error': 'unauthorized'}), 401
    return jsonify({
        'id': current_user.id,
        'role': current_user.role,
        'full_name': current_user.full_name,
        'username': current_user.username,
        'computer_id': current_user.computer_id or '',
    })


@app.route('/api/stats/today')
def api_stats_today():
    return jsonify(get_daily_stats())


@app.route('/api/order/files/<int:order_id>')
def api_order_files(order_id):
    files = OrderFile.query.filter_by(order_id=order_id).order_by(OrderFile.sort_order).all()
    return jsonify([{
        'id': f.id, 'file_name': f.file_name, 'file_type': f.file_type,
        'page_count': f.page_count, 'print_status': f.print_status
    } for f in files])


@app.route('/api/cashier/summary')
def api_cashier_summary():
    from datetime import date
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    orders = Order.query.filter(
        Order.created_at >= start,
        Order.created_at <= end
    ).all()
    cash_total = sum(o.amount_received or 0 for o in orders if o.payment_method == 'cash' and o.payment_status == 'paid')
    card_total = sum(o.amount_received or 0 for o in orders if o.payment_method == 'card' and o.payment_status == 'paid')
    free_count = sum(1 for o in orders if o.payment_method == 'free')
    unpaid_count = sum(1 for o in orders if o.payment_status == 'unpaid')
    return jsonify({
        'cash_total': cash_total,
        'card_total': card_total,
        'free_count': free_count,
        'unpaid_count': unpaid_count,
        'total_collected': cash_total + card_total
    })


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


# ====== Backups ======

@app.route('/manager/backups')
@login_required
@manager_required
def manager_backups():
    from backup import get_backup_list, check_backup_needed
    backups = get_backup_list()
    backup_needed = check_backup_needed()
    shop_name = get_setting('shop_name', config.SHOP_NAME)
    return render_template('manager_backups.html', backups=backups,
                           backup_needed=backup_needed, shop_name=shop_name)


@app.route('/manager/backups/now', methods=['POST'])
@login_required
@manager_required
def manager_backups_now():
    from backup import run_full_backup
    result = run_full_backup()
    return jsonify(result)


@app.route('/manager/backups/download/<filename>')
@login_required
@manager_required
def manager_backups_download(filename):
    from backup import BACKUP_DIR
    return send_from_directory(BACKUP_DIR, filename, as_attachment=True)


@app.route('/manager/backups/delete/<filename>', methods=['POST'])
@login_required
@manager_required
def manager_backups_delete(filename):
    from backup import BACKUP_DIR
    fp = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(fp):
        os.remove(fp)
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404


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
