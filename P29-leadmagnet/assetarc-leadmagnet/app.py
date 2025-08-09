
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from jinja2 import Template
from weasyprint import HTML
import tempfile

load_dotenv()
app=Flask(__name__); CORS(app)

FAQ={
    "what is section 42": "Asset-for-share rollover relief under the Income Tax Act.",
    "how do tokens work": "You prepay for advisory credits; each final document consumes one."
}

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/faq')
def faq():
    q=(request.get_json(force=True) or {}).get('q','').strip().lower()
    for k,v in FAQ.items():
        if k in q: return jsonify({'ok':True,'answer':v})
    return jsonify({'ok':True,'answer':"We'll get back to you with a detailed answer."})

@app.post('/suggest')
def suggest():
    data=request.get_json(force=True) or {}
    goal=(data.get('goal') or '').lower()
    if 'trust' in goal: svc='Trust Setup'
    elif 'offshore' in goal or 'ibc' in goal: svc='IBC Structuring'
    elif 'section 42' in goal or 's42' in goal: svc='Section 42 Rollover'
    else: svc='Company Setup'
    return jsonify({'ok':True,'recommended_service':svc})

@app.post('/leadmagnet/pdf')
def lead_pdf():
    data=request.get_json(force=True) or {}
    tpl_path=os.path.join('templates','leadmagnet.html')
    with open(tpl_path,'r',encoding='utf-8') as f:
        html=Template(f.read()).render(**data)
    out=os.path.join(tempfile.gettempdir(),'leadmagnet.pdf')
    HTML(string=html).write_pdf(out)
    return send_file(out, as_attachment=True, download_name='assetarc-leadmagnet.pdf')
