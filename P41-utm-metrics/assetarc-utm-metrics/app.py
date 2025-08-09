
import os, csv, io, tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from jinja2 import Template
from weasyprint import HTML

load_dotenv()
app=Flask(__name__); CORS(app)
DB=os.getenv('DB_URL','sqlite:///assetarc_metrics.db')
eng=create_engine(DB, future=True)
with eng.begin() as c:
    c.execute(text('''CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts DATETIME NOT NULL,
        event TEXT, source TEXT, medium TEXT, campaign TEXT, term TEXT, content TEXT,
        page TEXT, user_email TEXT, meta TEXT)'''))

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/track')
def track():
    b=request.get_json(force=True) or {}
    with eng.begin() as c:
        c.execute(text('INSERT INTO events(ts,event,source,medium,campaign,term,content,page,user_email,meta) VALUES (:ts,:e,:s,:m,:c,:t,:co,:p,:u,:meta)'),
            {'ts': datetime.utcnow(), 'e': b.get('event'), 's': b.get('utm_source'), 'm': b.get('utm_medium'),
             'c': b.get('utm_campaign'), 't': b.get('utm_term'), 'co': b.get('utm_content'), 'p': b.get('page'),
             'u': b.get('user_email'), 'meta': (b.get('meta') or '')})
    return jsonify({'ok':True})

@app.get('/export.csv')
def export_csv():
    buf=io.StringIO(); w=csv.writer(buf); w.writerow(['ts','event','source','medium','campaign','term','content','page','user_email'])
    with eng.begin() as c:
        for row in c.execute(text('SELECT ts,event,source,medium,campaign,term,content,page,user_email FROM events ORDER BY ts DESC')):
            w.writerow(row)
    buf.seek(0); return send_file(io.BytesIO(buf.getvalue().encode()), as_attachment=True, download_name='events.csv', mimetype='text/csv')

@app.post('/report/pdf')
def report_pdf():
    payload=request.get_json(force=True) or {}
    tpl=open(os.path.join('templates','utm_report.html'),'r',encoding='utf-8').read()
    html=Template(tpl).render(**payload)
    out=os.path.join(tempfile.gettempdir(),'utm-report.pdf')
    HTML(string=html).write_pdf(out)
    return send_file(out, as_attachment=True, download_name='utm-report.pdf')
