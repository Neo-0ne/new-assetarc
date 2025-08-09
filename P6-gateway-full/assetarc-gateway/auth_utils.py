
import os, jwt
from functools import wraps
from flask import request, jsonify

ACCESS_COOKIE = os.getenv('ACCESS_COOKIE', 'access_token')
JWT_SECRET   = os.getenv('JWT_SECRET', 'change_me')

def _token_from_request():
    tok = request.cookies.get(ACCESS_COOKIE)
    if tok: return tok
    h = request.headers.get('Authorization','')
    if h.lower().startswith('bearer '):
        return h.split(' ',1)[1].strip()
    return None

def current_user():
    tok = _token_from_request()
    if not tok: return None
    try:
        payload = jwt.decode(tok, JWT_SECRET, algorithms=['HS256'])
        if payload.get('type') != 'access':
            return None
        return payload
    except Exception:
        return None

def require_auth(fn):
    @wraps(fn)
    def _w(*a, **k):
        u = current_user()
        if not u:
            return jsonify({'ok': False, 'error':'Unauthorized'}), 401
        request.user = u
        return fn(*a, **k)
    return _w
