import os
from datetime import datetime, timedelta
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import config

db = SQLAlchemy()

class Worker(db.Model):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    computer_id = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='worker')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active_property(self):
        return self.is_active

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    computer_id = db.Column(db.String(10), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    file_name = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(10), nullable=True)
    copies = db.Column(db.Integer, default=1)
    color_mode = db.Column(db.String(10), default='bw')
    paper_size = db.Column(db.String(5), default='A4')
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='new')
    price = db.Column(db.Float, default=0)
    page_count = db.Column(db.Integer, default=0)
    is_duplex = db.Column(db.Boolean, default=False)
    duplex_status = db.Column(db.String(20), default='none')
    ai_suggestions = db.Column(db.Text, nullable=True)
    payment_status = db.Column(db.String(10), default='unpaid')
    payment_method = db.Column(db.String(10), default='cash')
    amount_received = db.Column(db.Float, default=0)
    change_given = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transfer(db.Model):
    __tablename__ = 'transfers'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    from_computer = db.Column(db.String(10), nullable=False)
    to_computer = db.Column(db.String(10), nullable=False)
    reason = db.Column(db.String(256), nullable=True)
    transferred_at = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Order', backref='transfers')


class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if not Worker.query.filter_by(username='admin').first():
            admin = Worker(
                username='admin',
                full_name='Manager',
                computer_id=None,
                role='manager',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        create_default_workers()


def create_default_workers():
    workers_data = [
        ('worker1', 'pass1', 'Worker 1', 'PC1'),
        ('worker2', 'pass2', 'Worker 2', 'PC2'),
        ('worker3', 'pass3', 'Worker 3', 'PC3'),
        ('worker4', 'pass4', 'Worker 4', 'PC4'),
    ]
    for username, password, full_name, computer_id in workers_data:
        if not Worker.query.filter_by(username=username).first():
            w = Worker(
                username=username,
                full_name=full_name,
                computer_id=computer_id,
                role='worker',
                is_active=True
            )
            w.set_password(password)
            db.session.add(w)
    db.session.commit()


def generate_order_number():
    today = datetime.utcnow().strftime('%Y%m%d')
    prefix = f"{today}-"
    last_order = Order.query.filter(
        Order.order_number.like(f"{prefix}%")
    ).order_by(Order.order_number.desc()).first()
    if last_order:
        last_num = int(last_order.order_number.split('-')[1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"{prefix}{new_num:04d}"


def auto_delete_old_files():
    cutoff = datetime.utcnow() - timedelta(days=config.AUTO_DELETE_DAYS)
    old_orders = Order.query.filter(
        Order.status == 'done',
        Order.created_at < cutoff
    ).all()
    for order in old_orders:
        if order.file_path and os.path.exists(order.file_path):
            try:
                os.remove(order.file_path)
            except OSError:
                pass
        db.session.delete(order)
    db.session.commit()


def get_daily_stats(date=None):
    if date is None:
        date = datetime.utcnow().date()
    start = datetime.combine(date, datetime.min.time())
    end = datetime.combine(date, datetime.max.time())
    orders = Order.query.filter(
        Order.created_at >= start,
        Order.created_at <= end
    ).all()
    total_orders = len(orders)
    total_pages = sum(
        (o.copies * o.page_count) if o.page_count else o.copies
        for o in orders
    )
    total_revenue = sum(o.price or 0 for o in orders)
    return {
        'orders': total_orders,
        'pages': total_pages,
        'revenue': total_revenue,
        'date': date
    }


def get_peak_hours(days=30):
    cutoff = datetime.utcnow() - timedelta(days=days)
    orders = Order.query.filter(Order.created_at >= cutoff).all()
    hour_counts = {}
    for o in orders:
        h = o.created_at.hour
        hour_counts[h] = hour_counts.get(h, 0) + 1
    return sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
