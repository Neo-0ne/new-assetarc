
import os, tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from jinja2 import Template
from weasyprint import HTML

load_dotenv()
app=Flask(__name__); CORS(app)

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/templates')
def t(): return jsonify({'ok':True,'templates':[n for n in os.listdir('templates') if n.endswith('.html')]})

@app.post('/render')
def render():
  b=request.get_json(force=True) or {}
  tid=b.get('template_id'); vars=b.get('vars',{})
  p=os.path.join('templates', tid or '')
  if not p.endswith('.html') or not os.path.exists(p): return jsonify({'ok':False,'error':'not found'}),404
  with open(p,'r',encoding='utf-8') as f: html=Template(f.read()).render(**vars)
  return jsonify({'ok':True,'html':html})

@app.post('/render/pdf')
def render_pdf():
  b=request.get_json(force=True) or {}
  tid=b.get('template_id'); vars=b.get('vars',{}); outn=b.get('output_name','marketing.pdf')
  p=os.path.join('templates', tid or '')
  if not p.endswith('.html') or not os.path.exists(p): return jsonify({'ok':False,'error':'not found'}),404
  with open(p,'r',encoding='utf-8') as f: html=Template(f.read()).render(**vars)
  out=os.path.join(tempfile.gettempdir(), outn if outn.endswith('.pdf') else outn+'.pdf')
  HTML(string=html).write_pdf(out)
  return send_file(out, as_attachment=True, download_name=os.path.basename(out))
