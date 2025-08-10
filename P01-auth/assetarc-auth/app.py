
import os, bcrypt, uuid
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
app=Flask(__name__); CORS(app, supports_credentials=True)
JWT_SECRET=os.getenv('JWT_SECRET','change')
ACCESS_TTL=int(os.getenv('ACCESS_TOKEN_TTL_MIN','15'))
REFRESH_TTL=int(os.getenv('REFRESH_TOKEN_TTL_DAYS','30'))
from itsdangerous import URLSafeTimedSerializer
signer=URLSafeTimedSerializer(JWT_SECRET)
eng=create_engine(os.getenv('SQLALCHEMY_DATABASE_URI','sqlite:///assetarc_auth.db'), future=True)
with eng.begin() as c:
    c.execute(text('CREATE TABLE IF NOT EXISTS users(email TEXT PRIMARY KEY, role TEXT, created_at DATETIME)'))
    c.execute(text('CREATE TABLE IF NOT EXISTS otps(email TEXT, hash BLOB, exp DATETIME)'))
    c.execute(text('CREATE TABLE IF NOT EXISTS refresh(jti TEXT PRIMARY KEY, email TEXT, exp DATETIME)'))

def _set_cookie(resp, name, val, max_age):
    resp.set_cookie(name, val, max_age=max_age, httponly=True, samesite='Lax', secure=os.getenv('COOKIE_SECURE','False').lower()=='true', domain=None if os.getenv('COOKIE_DOMAIN','localhost')=='localhost' else os.getenv('COOKIE_DOMAIN'))

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/auth/request-otp')
def req():
    email=(request.json or {}).get('email','').strip().lower()
    if not email: return jsonify({'ok':False,'error':'email required'}),400
    code=str(uuid.uuid4().int)[-6:]
    hashed=bcrypt.hashpw(code.encode(), bcrypt.gensalt())
    with eng.begin() as c:
        c.execute(text('INSERT OR REPLACE INTO users(email,role,created_at) VALUES (:e,:r,:t)'), {'e':email,'r':'client','t':datetime.utcnow()})
        c.execute(text('DELETE FROM otps WHERE email=:e'), {'e':email})
        c.execute(text('INSERT INTO otps(email,hash,exp) VALUES (:e,:h,:x)'), {'e':email,'h':hashed,'x':datetime.utcnow()+timedelta(minutes=int(os.getenv('OTP_TTL_MIN','10')))})
    # For demo, return the code (replace with SES send in production)
    return jsonify({'ok':True,'message':'OTP issued (demo returns it)','code':code})

@app.post('/auth/verify-otp')
def ver():
    email=(request.json or {}).get('email','').strip().lower()
    code=(request.json or {}).get('code','').strip()
    r=eng.execute(text('SELECT hash,exp FROM otps WHERE email=:e ORDER BY exp DESC LIMIT 1'), {'e':email}).fetchone()
    if not r: return jsonify({'ok':False,'error':'no otp'}),400
    if r[1] < datetime.utcnow(): return jsonify({'ok':False,'error':'expired'}),400
    if not bcrypt.checkpw(code.encode(), r[0]): return jsonify({'ok':False,'error':'invalid'}),400
    # issue cookie tokens using itsdangerous signer
    now=datetime.now(timezone.utc)
    access=signer.dumps({'sub':email,'type':'access','iat':now.isoformat()})
    refresh_id=uuid.uuid4().hex
    refresh=signer.dumps({'sub':email,'type':'refresh','jti':refresh_id,'iat':now.isoformat()})
    with eng.begin() as c:
        c.execute(text('INSERT INTO refresh(jti,email,exp) VALUES (:j,:e,:x)'), {'j':refresh_id,'e':email,'x': datetime.utcnow()+timedelta(days=REFRESH_TTL)})
    resp=jsonify({'ok':True,'user':{'email':email,'role':'client'}})
    _set_cookie(resp,'access_token',access,60*ACCESS_TTL)
    _set_cookie(resp,'refresh_token',refresh,60*60*24*REFRESH_TTL)
    return resp

@app.post('/auth/refresh')
def refresh():
    tok=request.cookies.get('refresh_token')
    if not tok: return jsonify({'ok':False}),401
    import itsdangerous
    try:
        payload=signer.loads(tok, max_age=60*60*24*REFRESH_TTL)
    except itsdangerous.BadSignature:
        return jsonify({'ok':False}),401
    jti=payload.get('jti'); email=payload.get('sub')
    r=eng.execute(text('SELECT 1 FROM refresh WHERE jti=:j AND exp> :now'), {'j':jti,'now':datetime.utcnow()}).fetchone()
    if not r: return jsonify({'ok':False}),401
    now=datetime.now(timezone.utc)
    access=signer.dumps({'sub':email,'type':'access','iat':now.isoformat()})
    resp=jsonify({'ok':True}); _set_cookie(resp,'access_token',access,60*ACCESS_TTL); return resp

@app.get('/auth/user')
def me():
    tok=request.cookies.get('access_token')
    if not tok: return jsonify({'ok':False}),401
    import itsdangerous
    try:
        payload=signer.loads(tok, max_age=60*ACCESS_TTL*2)
    except itsdangerous.BadSignature:
        return jsonify({'ok':False}),401
    if payload.get('type')!='access': return jsonify({'ok':False}),401
    return jsonify({'ok':True,'user':{'email':payload.get('sub'),'role':'client'}})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5001')), debug=os.getenv('FLASK_ENV')=='development')
