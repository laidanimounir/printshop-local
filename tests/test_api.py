import json


def test_api_login_success(client):
    response = client.post('/api/login', json={
        'username': 'worker1',
        'password': 'pass1',
    })
    data = response.get_json()
    assert response.status_code == 200
    assert data['success'] is True
    assert data['id'] == 2
    assert data['role'] == 'worker'
    assert data['full_name'] == 'Worker 1'
    assert data['computer_id'] == 'PC1'
    assert data['username'] == 'worker1'


def test_api_login_failure(client):
    response = client.post('/api/login', json={
        'username': 'worker1',
        'password': 'wrong',
    })
    data = response.get_json()
    assert response.status_code == 401
    assert data['success'] is False
    assert 'message' in data


def test_api_me_authenticated(client):
    client.post('/api/login', json={'username': 'worker1', 'password': 'pass1'})
    response = client.get('/api/me')
    data = response.get_json()
    assert response.status_code == 200
    assert data['id'] == 2
    assert data['role'] == 'worker'
    assert data['full_name'] == 'Worker 1'


def test_api_me_unauthenticated(client):
    response = client.get('/api/me')
    data = response.get_json()
    assert response.status_code == 401
    assert data['error'] == 'unauthorized'


def test_api_workers_manager(client):
    client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    response = client.get('/api/workers')
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) >= 1


def test_api_customers_manager(client):
    client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    response = client.get('/api/customers')
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)


def test_api_orders_all_manager(client):
    client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
    response = client.get('/api/orders/all')
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, list)
