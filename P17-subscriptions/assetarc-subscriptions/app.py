
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
app=Flask(__name__); CORS(app)
eng=create_engine(os.getenv('DB_URL','sqlite:///assetarc_subs.db'), future=True)
with eng.begin() as c:
    c.execute(text('''CREATE TABLE IF NOT EXISTS tiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, monthly_tokens INTEGER, price REAL)'''))
    c.execute(text('''CREATE TABLE IF NOT EXISTS subs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, tier_id INTEGER, tokens_left INTEGER, started_at DATETIME DEFAULT CURRENT_TIMESTAMP)'''))

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/tier')
def create_tier():
    b=request.get_json(force=True) or {}
    with eng.begin() as c:
        c.execute(text('INSERT INTO tiers(name,monthly_tokens,price) VALUES (:n,:t,:p)'),
                  {'n':b.get('name'),'t':int(b.get('monthly_tokens',0)),'p':float(b.get('price',0))})
    return jsonify({'ok':True})

@app.post('/subscribe')
def subscribe():
    b=request.get_json(force=True) or {}
    # assume payment already confirmed by P7
    with eng.begin() as c:
        c.execute(text('INSERT INTO subs(email,tier_id,tokens_left) VALUES (:e,:tid,(SELECT monthly_tokens FROM tiers WHERE id=:tid))'),
                  {'e':b.get('email'),'tid':int(b.get('tier_id'))})
    return jsonify({'ok':True})

@app.post('/mint')
def mint():
    b=request.get_json(force=True) or {}
    with eng.begin() as c:
        c.execute(text('UPDATE subs SET tokens_left=tokens_left+:a WHERE email=:e AND tier_id=:tid'),
                  {'a':int(b.get('amount',0)),'e':b.get('email'),'tid':int(b.get('tier_id'))})
    return jsonify({'ok':True})

@app.get('/balance')
def bal():
    email=request.args.get('email'); tid=int(request.args.get('tier_id','0'))
    with eng.begin() as c:
        r=c.execute(text('SELECT tokens_left FROM subs WHERE email=:e AND tier_id=:tid ORDER BY id DESC LIMIT 1'),
                    {'e':email,'tid':tid}).fetchone()
    return jsonify({'ok':True,'email':email,'tokens_left': (int(r[0]) if r else 0)})
