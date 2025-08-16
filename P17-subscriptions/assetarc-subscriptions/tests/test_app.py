import os
import importlib
import sys
from pathlib import Path
import pytest

# Ensure the application module can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / 'test.db'
    os.environ['DB_URL'] = f'sqlite:///{db_path}'
    import app
    importlib.reload(app)
    app.app.config['TESTING'] = True
    return app.app.test_client()


def test_create_tier(client):
    resp = client.post('/tier', json={'name': 'Basic', 'monthly_tokens': 100, 'price': 9.99})
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True


def test_subscribe_user(client):
    client.post('/tier', json={'name': 'Pro', 'monthly_tokens': 100, 'price': 10})
    resp = client.post('/subscribe', json={'email': 'user@example.com', 'tier_id': 1})
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True

    resp = client.get('/balance', query_string={'email': 'user@example.com', 'tier_id': 1})
    data = resp.get_json()
    assert data['ok'] is True
    assert data['tokens_left'] == 100


def test_mint_updates_balance(client):
    client.post('/tier', json={'name': 'Pro', 'monthly_tokens': 100, 'price': 10})
    client.post('/subscribe', json={'email': 'user@example.com', 'tier_id': 1})
    resp = client.post('/mint', json={'email': 'user@example.com', 'tier_id': 1, 'amount': 50})
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True

    resp = client.get('/balance', query_string={'email': 'user@example.com', 'tier_id': 1})
    data = resp.get_json()
    assert data['tokens_left'] == 150
