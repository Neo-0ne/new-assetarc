
import os, hmac, hashlib, json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import text as sql
from auth_middleware import require_auth, current_user
from db import init_db, Session
from google_availability import business_slots
load_dotenv()
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)
TOK_BASE=os.getenv('TOKENS_BASE','')
TOK_KEY=os.getenv('TOKENS_INTERNAL_KEY','')
CAL_SECRET=os.getenv('CALENDLY_SIGNING_SECRET','')
CAL_ID=os.getenv('GOOGLE_CALENDAR_ID','primary')
TZ=os.getenv('BUSINESS_TZ','Africa/Johannesburg')
WINDOW=os.getenv('BUSINESS_HOURS','09:00-16:00')
@app.before_first_request
def _init(): init_db()
@app.get('/healthz')
def h(): return jsonify({'ok':True})
@app.get('/availability')
def avail():
    f=request.args.get('from'); t=request.args.get('to')
    if not f or not t:
        return jsonify({'ok':True,'slots':[{'label':'Weekdays 09:00–16:00 (SAST)'}],'note':'Google not queried (from/to not provided).'})
    try:
        slots=business_slots(f,t,CAL_ID,TZ,WINDOW)
        return jsonify({'ok':True,'slots':slots,'tz':TZ})
    except Exception as e:
        return jsonify({'ok':True,'slots':[{'label':'Weekdays 09:00–16:00 (SAST)'}],'error':str(e)})
def _tokens_balance(email:str)->int:
    if not TOK_BASE: return 0
    import requests
    try:
        r=requests.get(TOK_BASE.rstrip('/')+f'/tokens/balance?email={email}', headers={'Authorization':f'Bearer {TOK_KEY}'}, timeout=6)
        if r.status_code==200: return int(r.json().get('balance',0))
    except requests.RequestException as e:
        app.logger.error('Token balance lookup failed: %s', e)
    return 0
@app.get('/entitlements')
@require_auth
def ents():
    s=Session()
    email=(getattr(request,'user',{}) or {}).get('sub')
    row=s.execute(sql('SELECT credits FROM entitlements WHERE email=:e'),{'e':email}).fetchone()
    credits=row[0] if row else 0
    tokens=_tokens_balance(email)
    return jsonify({'ok':True,'email':email,'credits':int(credits),'tokens':int(tokens),'has_access': (credits>0 or tokens>0)})
@app.post('/entitlements/grant')
def grant():
    auth=request.headers.get('Authorization','')
    user=current_user(); allowed=False
    if auth.lower().startswith('bearer ') and auth.split(' ',1)[1].strip()==os.getenv('TOKENS_INTERNAL_KEY',''): allowed=True
    if user and user.get('role') in ('owner_admin',): allowed=True
    if not allowed: return jsonify({'ok':False,'error':'Forbidden'}),403
    body=request.get_json(force=True) or {}
    email=body.get('email'); amount=int(body.get('amount',1))
    if not email: return jsonify({'ok':False,'error':'email required'}),400
    s=Session()
    cur=s.execute(sql('SELECT credits FROM entitlements WHERE email=:e'),{'e':email}).fetchone()
    if cur: s.execute(sql('UPDATE entitlements SET credits=credits+:a, updated_at=CURRENT_TIMESTAMP WHERE email=:e'),{'a':amount,'e':email})
    else: s.execute(sql('INSERT INTO entitlements(email,credits) VALUES (:e,:a)'),{'e':email,'a':amount})
    s.commit(); return jsonify({'ok':True})
def _verify_calendly(req)->bool:
    if not CAL_SECRET: return True
    sig=req.headers.get('Calendly-Webhook-Signature','')
    if not sig: return False
    try:
        parts=dict(kv.split('=') for kv in sig.split(','))
        v1=parts.get('v1',''); t=parts.get('t','')
        mac=hmac.new(CAL_SECRET.encode('utf-8'), (t+'.'+req.get_data(as_text=True)).encode('utf-8'), hashlib.sha256).hexdigest()
        return hmac.compare_digest(v1, mac)
    except Exception: return False
@app.post('/webhook/calendly')
def wh_cal():
    if not _verify_calendly(request):
        return jsonify({'ok':False,'error':'bad signature'}),400
    payload=request.get_json(force=True) or {}
    event=payload.get('event') or payload.get('event_type')
    data=payload.get('payload') or payload
    status='created' if 'created' in str(event).lower() else ('canceled' if 'cancel' in str(event).lower() else 'unknown')
    email=None
    try:
        email=(data.get('invitee',{}) or {}).get('email') or (data.get('email') if isinstance(data,dict) else None)
    except (AttributeError, TypeError) as e:
        app.logger.warning('Could not extract email from Calendly payload: %s', e)
    s=Session()
    s.execute(sql('INSERT INTO events(calendly_event, invitee_email, status, payload) VALUES (:ev,:em,:st,:pl)'),
              {'ev':str(event),'em':email or '', 'st':status, 'pl':json.dumps(payload)})
    if status=='created' and email:
        cur=s.execute(sql('SELECT credits FROM entitlements WHERE email=:e'),{'e':email}).fetchone()
        if cur and cur[0]>0:
            s.execute(sql('UPDATE entitlements SET credits=credits-1, updated_at=CURRENT_TIMESTAMP WHERE email=:e'),{'e':email})
    s.commit(); return jsonify({'ok':True})
if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5012')), debug=os.getenv('FLASK_ENV')=='development')
