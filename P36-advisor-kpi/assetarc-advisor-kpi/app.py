
import os, tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from jinja2 import Template
from weasyprint import HTML

load_dotenv()
app=Flask(__name__); CORS(app)
TOK=os.getenv('TOKENS_BASE','http://localhost:5007')

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/kpi/summary')
def kpi():
    # Minimal demo: pull a couple of balances to illustrate aggregation
    emails=request.args.get('emails','').split(',')
    data=[]
    for e in [x.strip() for x in emails if x.strip()]:
        try:
            r=requests.get(TOK.rstrip('/')+f'/tokens/balance?email={e}', timeout=5).json()
            data.append({'email':e,'balance':r.get('balance',0)})
        except Exception:
            data.append({'email':e,'balance':None})
    totals=sum([d['balance'] or 0 for d in data])
    return jsonify({'ok':True,'totals':totals,'rows':data})

@app.post('/kpi/export/pdf')
def export_pdf():
    payload=request.get_json(force=True) or {}
    tpl=open(os.path.join('templates','kpi_report.html'),'r',encoding='utf-8').read()
    html=Template(tpl).render(**payload)
    out=os.path.join(tempfile.gettempdir(),'advisor-kpi.pdf')
    HTML(string=html).write_pdf(out)
    return send_file(out, as_attachment=True, download_name='advisor-kpi.pdf')
