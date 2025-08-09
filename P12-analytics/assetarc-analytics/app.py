
import os, tempfile
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from jinja2 import Template
from weasyprint import HTML

load_dotenv()
app=Flask(__name__); CORS(app)

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/report/pdf')
def pdf():
  data=request.get_json(force=True) or {}
  tpl=open(os.path.join('templates','analytics_report.html'),'r',encoding='utf-8').read()
  html=Template(tpl).render(**data)
  out=os.path.join(tempfile.gettempdir(),'analytics.pdf')
  HTML(string=html).write_pdf(out)
  return send_file(out, as_attachment=True, download_name='analytics.pdf')
