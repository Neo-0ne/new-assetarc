
import os, jwt
from functools import wraps
from flask import request, jsonify

ACCESS_COOKIE=os.getenv('ACCESS_COOKIE','access_token')
JWT_SECRET=os.getenv('JWT_SECRET','change_me')

def _token():
    t=request.cookies.get(ACCESS_COOKIE)
    if t: return t
    h=request.headers.get('Authorization','')
    if h.lower().startswith('bearer '): return h.split(' ',1)[1].strip()
    return None

def require_auth(fn):
    @wraps(fn)
    def _w(*a, **k):
        t=_token()
        if not t: return jsonify({'ok':False,'error':'Unauthorized'}),401
        try:
            u=jwt.decode(t, JWT_SECRET, algorithms=['HS256'])
        except Exception:
            return jsonify({'ok':False,'error':'Unauthorized'}),401
        request.user=u
        return fn(*a, **k)
    return _w
