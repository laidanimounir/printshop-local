import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app import app as flask_app
from database import db, Worker

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret'

    with flask_app.app_context():
        db.init_app(flask_app)
        db.create_all()
        admin = Worker(username='admin', full_name='Admin', role='manager')
        admin.set_password('admin123')
        worker = Worker(username='worker1', full_name='Worker 1', role='worker', computer_id='PC1')
        worker.set_password('pass1')
        db.session.add(admin)
        db.session.add(worker)
        db.session.commit()

    yield flask_app

    with flask_app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
