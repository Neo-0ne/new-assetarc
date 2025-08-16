
import os, tempfile, datetime, hmac, hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import text as sql
from pydantic import BaseModel, ValidationError
from db import init_db, Session
from invoice import render_invoice_pdf, upload_invoice

load_dotenv()
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)

@app.before_first_request
def _init(): init_db()

@app.get('/healthz')
def h(): return jsonify({'ok':True})

def _grant(email:str, amount:int, reason:str='payment'):
    s=Session()
    cur=s.execute(sql('SELECT balance FROM tokens WHERE email=:e'),{'e':email}).fetchone()
    if cur: s.execute(sql('UPDATE tokens SET balance=balance+:a, updated_at=CURRENT_TIMESTAMP WHERE email=:e'),{'a':amount,'e':email})
    else: s.execute(sql('INSERT INTO tokens(email,balance) VALUES (:e,:a)'),{'e':email,'a':amount})
    s.commit()

def _consume(email:str, amount:int, reason:str='usage')->bool:
    s=Session()
    cur=s.execute(sql('SELECT balance FROM tokens WHERE email=:e'),{'e':email}).fetchone()
    if not cur or int(cur[0])<amount: return False
    s.execute(sql('UPDATE tokens SET balance=balance-:a, updated_at=CURRENT_TIMESTAMP WHERE email=:e'),{'a':amount,'e':email}); s.commit(); return True

@app.get('/tokens/balance')
def bal():
    email=request.args.get('email','')
    s=Session()
    cur=s.execute(sql('SELECT balance FROM tokens WHERE email=:e'),{'e':email}).fetchone()
    return jsonify({'ok':True,'email':email,'balance': int(cur[0]) if cur else 0})

class GrantBody(BaseModel):
    email:str
    amount:int
    reason:str|None=None

@app.post('/tokens/grant')
def grant():
    try: b=GrantBody(**request.get_json(force=True))
    except ValidationError as e: return jsonify({'ok':False,'error':e.errors()}),400
    _grant(b.email, b.amount, b.reason or 'manual')
    return jsonify({'ok':True})

class ConsumeBody(BaseModel):
    email:str
    amount:int
    reason:str|None=None

@app.post('/tokens/consume')
def consume():
    try: b=ConsumeBody(**request.get_json(force=True))
    except ValidationError as e: return jsonify({'ok':False,'error':e.errors()}),400
    ok=_consume(b.email, b.amount, b.reason or 'usage')
    if not ok: return jsonify({'ok':False,'error':'insufficient balance'}),402
    return jsonify({'ok':True})

# --- Checkout stubs (frontends handle actual redirects) ---
@app.post('/checkout/yoco')
def checkout_yoco():
    body=request.get_json(force=True) or {}
    # In production, call Yoco Sessions/SDK to create checkout link
    return jsonify({'ok':True,'redirect_url':'https://pay.yoco.com/your-link','amount':body.get('amount'), 'currency': body.get('currency','ZAR')})

@app.post('/checkout/nowpayments')
def checkout_np():
    body=request.get_json(force=True) or {}
    return jsonify({'ok':True,'invoice_url':'https://nowpayments.io/invoice/demo','amount':body.get('amount'), 'currency': body.get('currency','USD')})

# --- Webhooks (simulate verification) ---
@app.post('/webhook/yoco')
def wh_yoco():
    raw=request.get_data()
    secret=os.getenv('YOCO_WEBHOOK_SECRET','')
    sig=request.headers.get('X-Yoco-Signature','')
    mac=hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest() if secret else ''
    if secret and not hmac.compare_digest(sig, mac):
        app.logger.warning('Invalid Yoco signature')
        return jsonify({'ok':False,'error':'bad signature'}),403
    payload=request.get_json(force=True) or {}
    email=payload.get('email') or (payload.get('metadata') or {}).get('email') or 'client@example.com'
    tokens=int((payload.get('metadata') or {}).get('tokens',1))
    _grant(email, tokens, 'yoco_payment')
    # Build invoice
    out=os.path.join(tempfile.gettempdir(), f"invoice-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.pdf")
    values={'client_email':email,'client_name':payload.get('name','Client'),
            'date': datetime.datetime.utcnow().strftime('%Y-%m-%d'),
            'items':[{'desc':'Advisory Credit','qty':tokens,'unit': float(payload.get('amount',0))/max(tokens,1)}],
            'total': float(payload.get('amount',0))}
    render_invoice_pdf(values, os.path.join('templates','invoice.html'), out)
    s3key=upload_invoice(out, email)
    return jsonify({'ok':True,'granted':tokens,'invoice_s3_key':s3key})

@app.post('/webhook/nowpayments')
def wh_np():
    payload=request.get_json(force=True) or {}
    email=payload.get('customer_email','client@example.com')
    tokens=int((payload.get('order_description') or '1').split(' ')[0]) if isinstance(payload.get('order_description'),str) else 1
    _grant(email, tokens, 'crypto_payment')
    return jsonify({'ok':True,'granted':tokens})
