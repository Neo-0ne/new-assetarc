
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from auth_utils import require_auth, current_user
from service_client import forward_json

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)

AUTH=os.getenv('AUTH_BASE','http://localhost:5001')
LLM=os.getenv('LLM_BASE','http://localhost:5002')
FX =os.getenv('FX_BASE','http://localhost:5003')
PAY=os.getenv('PAY_BASE','http://localhost:5011')
BOOK=os.getenv('BOOKING_BASE','http://localhost:5012')

@app.get('/healthz')
def health(): return jsonify({'ok':True})

@app.get('/user')
def user():
    u = current_user()
    if not u: return jsonify({'ok': False}), 401
    return jsonify({'ok': True, 'user': {'email': u.get('sub'), 'role': u.get('role')}})

# -------- Bridge: FX --------
@app.get('/bridge/fx/latest')
@require_auth
def b_fx_latest():
    base = request.args.get('base','USD')
    symbols = request.args.get('symbols','ZAR')
    # forward to FX
    return forward_json(FX, 'GET', f"/fx/latest?base={base}&symbols={symbols}")

@app.post('/bridge/fx/lock')
@require_auth
def b_fx_lock():
    return forward_json(FX, 'POST', "/fx/lock", request.get_json(force=True))

# -------- Bridge: Payments --------
@app.post('/bridge/payments/create-invoice/nowpayments')
@require_auth
def b_pay_invoice():
    return forward_json(PAY, 'POST', "/payments/create-invoice/nowpayments", request.get_json(force=True))

# -------- Bridge: Booking --------
@app.get('/bridge/booking/availability')
@require_auth
def b_booking_avail():
    # If your Booking microservice exposes `/availability?from=...&to=...`
    return forward_json(BOOK, 'GET', f"/availability?from={request.args.get('from','')}&to={request.args.get('to','')}")

# -------- Bridge: LLM --------
@app.post('/bridge/llm/generate')
@require_auth
def b_llm_generate():
    return forward_json(LLM, 'POST', "/llm/generate", request.get_json(force=True))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5010')), debug=os.getenv('FLASK_ENV')=='development')
