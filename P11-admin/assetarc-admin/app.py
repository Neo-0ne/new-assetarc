
import os, json, requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)
SERVICES=json.loads(os.getenv('SERVICES_JSON','[]'))

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/status')
def status():
    out=[]
    for s in SERVICES:
        try:
            r=requests.get(s['url'], timeout=3)
            ok=(r.status_code==200 and (r.json().get('ok') if r.headers.get('content-type','').startswith('application/json') else True))
        except Exception:
            ok=False
        out.append({'name':s['name'], 'url':s['url'], 'ok':ok})
    return jsonify({'ok':True,'services':out})

@app.get('/')
def index():
    return send_from_directory('static', 'index.html')
