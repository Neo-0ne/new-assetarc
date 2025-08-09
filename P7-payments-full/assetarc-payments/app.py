
import os, time, hmac, hashlib, jwt, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)

JWT_SECRET=os.getenv('JWT_SECRET','change_me')
ACCESS_COOKIE=os.getenv('ACCESS_COOKIE','access_token')

NOW_API=os.getenv('NOWPAY_API_KEY','')
NOW_IPN_SECRET=os.getenv('NOWPAY_IPN_SECRET','')
YOCO_WH=os.getenv('YOCO_WEBHOOK_SECRET','')

TOK_BASE=os.getenv('TOKENS_BASE','http://tokens.asset-arc.local')
TOK_KEY=os.getenv('TOKENS_INTERNAL_KEY','change_me_internal_secret')

def _user_from_cookie():
    tok=request.cookies.get(ACCESS_COOKIE)
    if not tok: return None
    try: return jwt.decode(tok, JWT_SECRET, algorithms=['HS256'])
    except Exception: return None

def _mint(email, amount=1, meta=None):
    try:
        r=requests.post(TOK_BASE.rstrip('/')+'/tokens/mint',
                        json={'email':email,'amount':amount,'meta':meta or {}},
                        headers={'Authorization':f'Bearer {TOK_KEY}'}, timeout=8)
        ok = (r.status_code == 200 and (r.json().get('ok') is True))
        return ok
    except Exception:
        return False

@app.get('/healthz')
def health(): return jsonify({'ok':True})

# ---------- Create NOWPayments invoice ----------
@app.post('/payments/create-invoice/nowpayments')
def create_now_invoice():
    u=_user_from_cookie()
    if not u: return jsonify({'ok':False,'error':'Unauthorized'}),401
    if not NOW_API: return jsonify({'ok':False,'error':'NOWPAYMENTS key missing'}),400
    data=request.get_json(force=True) or {}
    amount=data.get('amount')
    currency=(data.get('currency') or 'ZAR').upper()
    order_id=data.get('order_id') or f"ord_{int(time.time())}"
    description=(data.get('description') or 'AssetArc Service') + f" |email={u.get('sub','client@example.com')}"
    payload={
        "price_amount": amount,
        "price_currency": currency,
        "order_id": order_id,
        "order_description": description,
        "ipn_callback_url": data.get('ipn') or "https://pay.asset-arc.com/webhook/nowpayments",
        "success_url": data.get('success') or "https://app.asset-arc.com/paid",
        "cancel_url": data.get('cancel') or "https://app.asset-arc.com/cancelled"
    }
    try:
        r=requests.post('https://api.nowpayments.io/v1/invoice',
                        headers={'x-api-key':NOW_API,'Content-Type':'application/json'},
                        json=payload, timeout=15)
        js=r.json()
        if r.status_code>=300:
            return jsonify({'ok':False,'error':'NOWPayments create failed','detail':js}), r.status_code
        return jsonify({'ok':True,'invoice':js})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)}),502

# ---------- NOWPayments webhook (IPN) ----------
@app.post('/webhook/nowpayments')
def wh_now():
    # If IPN secret provided, verify HMAC SHA512 of raw body
    if NOW_IPN_SECRET:
        sig=request.headers.get('x-nowpayments-sig','')
        calc=hmac.new(NOW_IPN_SECRET.encode('utf-8'), request.get_data(), hashlib.sha512).hexdigest()
        if sig and sig != calc:
            return jsonify({'ok':False,'error':'bad signature'}),400
    js=request.get_json(force=True) or {}
    status=(js.get('payment_status') or '').lower()
    email='client@example.com'
    # Pass email in description as "|email=<addr>"
    desc=js.get('order_description') or ''
    if '|email=' in desc:
        email=desc.split('|email=')[-1].strip()
    if status in ('finished','confirmed'):
        _mint(email, amount=1, meta={
            'order_id': js.get('order_id'),
            'method': 'crypto',
            'amount': js.get('price_amount'),
            'currency': js.get('price_currency'),
            'tx': js.get('payment_id') or js.get('invoice_id')
        })
    return jsonify({'ok':True})

# ---------- Yoco webhook (Card) ----------
@app.post('/webhook/yoco')
def wh_yoco():
    # If secret provided, verify signature header presence; exact computation may vary by Yoco version.
    if YOCO_WH and not request.headers.get('X-Yoco-Signature'):
        return jsonify({'ok':False,'error':'missing signature'}),400
    js=request.get_json(force=True) or {}
    data=js.get('data') or js  # some Yoco posts nest under "data"
    status=(str(data.get('status') or '')).lower()
    email=(data.get('customer') or {}).get('email') or 'client@example.com'
    if status in ('successful','succeeded','paid','complete','completed'):
        _mint(email, amount=1, meta={
            'method':'card',
            'processor':'yoco',
            'amount': data.get('amount') or data.get('amount_charged'),
            'currency': data.get('currency') or 'ZAR',
            'raw_id': data.get('id') or data.get('payment_id')
        })
    return jsonify({'ok':True})
