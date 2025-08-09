
import os, tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from jinja2 import Template
from weasyprint import HTML

load_dotenv()
app=Flask(__name__); CORS(app)
eng=create_engine(os.getenv('DB_URL','sqlite:///assetarc_review.db'), future=True)
with eng.begin() as c:
    c.execute(text('''CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_key TEXT, client_email TEXT, reason TEXT, status TEXT DEFAULT 'open',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)'''))

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/flag')
def flag():
    b=request.get_json(force=True) or {}
    with eng.begin() as c:
        c.execute(text('INSERT INTO reviews(doc_key,client_email,reason) VALUES (:k,:e,:r)'),
                  {'k':b.get('doc_key'),'e':b.get('client_email'),'r':b.get('reason')})
    return jsonify({'ok':True})

@app.get('/list')
def list():
    rows=[]
    with eng.begin() as c:
        for r in c.execute(text('SELECT id,doc_key,client_email,reason,status,created_at FROM reviews ORDER BY id DESC')):
            rows.append({'id':r[0],'doc_key':r[1],'client_email':r[2],'reason':r[3],'status':r[4],'created_at':str(r[5])})
    return jsonify({'ok':True,'rows':rows})

@app.post('/export/pdf')
def export():
    data=request.get_json(force=True) or {}
    tpl=open(os.path.join('templates','review_summary.html'),'r',encoding='utf-8').read()
    html=Template(tpl).render(**data)
    out=os.path.join(tempfile.gettempdir(),'review-summary.pdf')
    HTML(string=html).write_pdf(out)
    return send_file(out, as_attachment=True, download_name='review-summary.pdf')
