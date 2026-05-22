from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, Worker

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()
login_manager.login_view = 'auth.worker_login'


@login_manager.user_loader
def load_user(user_id):
    return Worker.query.get(int(user_id))


def worker_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.worker_login'))
        if current_user.role not in ('worker', 'manager'):
            flash('Access denied. Worker privileges required.', 'danger')
            return redirect(url_for('auth.worker_login'))
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.worker_login'))
        if current_user.role != 'manager':
            flash('Access denied. Manager privileges required.', 'danger')
            return redirect(url_for('auth.worker_login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/worker/login', methods=['GET', 'POST'])
def worker_login():
    if current_user.is_authenticated:
        if current_user.role == 'manager':
            return redirect(url_for('manager_dashboard'))
        return redirect(url_for('worker_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        worker = Worker.query.filter_by(username=username, is_active=True).first()
        if worker and worker.check_password(password):
            login_user(worker, remember=remember)
            next_page = request.args.get('next')
            if current_user.role == 'manager':
                return redirect(next_page or url_for('manager_dashboard'))
            return redirect(next_page or url_for('worker_dashboard'))
        
        flash('Invalid username or password.', 'danger')
    
    return render_template('worker_login.html')


@auth_bp.route('/worker/logout')
@login_required
def worker_logout():
    logout_user()
    return redirect(url_for('auth.worker_login'))


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Request must be JSON'}), 400
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    worker = Worker.query.filter_by(username=username, is_active=True).first()
    if worker and worker.check_password(password):
        login_user(worker)
        return jsonify({
            'success': True,
            'id': worker.id,
            'role': worker.role,
            'full_name': worker.full_name,
            'computer_id': worker.computer_id or '',
            'username': worker.username,
        })
    return jsonify({'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
