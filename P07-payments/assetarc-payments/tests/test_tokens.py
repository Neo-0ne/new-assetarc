import os, sys, tempfile
from pathlib import Path
from sqlalchemy import text
import flask

# Restore removed decorator for Flask 3 compatibility
if not hasattr(flask.Flask, 'before_first_request'):
    def before_first_request(self, f):
        self.before_request(f)
        return f
    flask.Flask.before_first_request = before_first_request

# Ensure module import paths and working directory
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.modules.pop('db', None)

# Configure isolated SQLite database
DB_PATH = os.path.join(tempfile.gettempdir(), 'payments_test.db')
os.environ['PAY_DB_URL'] = f'sqlite:///{DB_PATH}'

from db import init_db, Session
from app import app, _grant, _consume

# Initialize database tables
init_db()

def test_grant_and_consume_update_balance():
    email = 'user@example.com'
    s = Session()
    s.execute(text('DELETE FROM tokens'))
    s.commit()
    _grant(email, 10, 'test')
    bal = s.execute(text('SELECT balance FROM tokens WHERE email=:e'), {'e': email}).fetchone()[0]
    assert bal == 10
    ok = _consume(email, 3, 'test')
    assert ok
    bal = s.execute(text('SELECT balance FROM tokens WHERE email=:e'), {'e': email}).fetchone()[0]
    assert bal == 7


def test_consume_endpoint_insufficient():
    s = Session()
    s.execute(text('DELETE FROM tokens'))
    s.commit()
    client = app.test_client()
    email = 'client@example.com'
    resp = client.post('/tokens/consume', json={'email': email, 'amount': 5})
    assert resp.status_code == 402
    _grant(email, 5, 'test')
    resp = client.post('/tokens/consume', json={'email': email, 'amount': 5})
    assert resp.status_code == 200
    bal = s.execute(text('SELECT balance FROM tokens WHERE email=:e'), {'e': email}).fetchone()[0]
    assert bal == 0
