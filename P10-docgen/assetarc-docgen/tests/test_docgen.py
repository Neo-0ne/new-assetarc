import os, sys, tempfile
from pathlib import Path
import jwt
from sqlalchemy import text
import flask

# Restore removed decorator for Flask 3 compatibility
if not hasattr(flask.Flask, 'before_first_request'):
    def before_first_request(self, f):
        self.before_request(f)
        return f
    flask.Flask.before_first_request = before_first_request

# Ensure module import paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.pop('db', None)

# Configure environment
DB_PATH = os.path.join(tempfile.gettempdir(), 'docgen_test.db')
os.environ['DOCGEN_DB_URL'] = f'sqlite:///{DB_PATH}'
os.environ['JWT_SECRET'] = 'test-secret'
os.environ['ENTITLEMENT_REQUIRED'] = 'True'

import app as docgen_app
docgen_app.TEMPLATES_DIR = os.path.join(ROOT, 'templates')
app = docgen_app.app
from db import init_db, Session
from entitlement import grant

# Initialize database tables
init_db()

def _headers(email='user@example.com'):
    token = jwt.encode({'sub': email, 'type': 'access'}, 'test-secret', algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


def test_generate_docx_requires_entitlement_and_succeeds_after_grant():
    init_db()
    s = Session()
    s.execute(text('DELETE FROM credits'))
    s.commit()
    client = app.test_client()
    data = {
        'template_id': 'company_resolution.docx',
        'values': {},
        'output_name': 'out.docx',
        'consume_token': True,
    }
    headers = _headers()
    resp = client.post('/generate/docx', json=data, headers=headers)
    assert resp.status_code == 402
    grant('user@example.com', 1)
    resp = client.post('/generate/docx', json=data, headers=headers)
    assert resp.status_code == 200
    s = Session()
    bal = s.execute(text('SELECT amount FROM credits WHERE email=:e'), {'e': 'user@example.com'}).fetchone()[0]
    assert bal == 0
