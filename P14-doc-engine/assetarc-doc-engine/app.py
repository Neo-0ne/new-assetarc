
import os, tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from jinja2 import Template
from docx import Document
from weasyprint import HTML

load_dotenv()
app=Flask(__name__); CORS(app, supports_credentials=True)

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/templates')
def list_t():
    return jsonify({'ok':True,'templates':[n for n in os.listdir('templates') if n.endswith('.docx') or n.endswith('.html')]})

@app.post('/generate/docx')
def gen_docx():
    b=request.get_json(force=True) or {}
    tid=b.get('template_id'); vals=b.get('values',{})
    p=os.path.join('templates', tid or '')
    if not p.endswith('.docx') or not os.path.exists(p): return jsonify({'ok':False,'error':'template not found'}),404
    doc=Document(p)
    for pgh in doc.paragraphs:
        for k,v in vals.items():
            if f'{{{{{k}}}}}' in pgh.text:
                for r in pgh.runs: r.text=r.text.replace(f'{{{{{k}}}}}', str(v))
    out=os.path.join(tempfile.gettempdir(), (b.get('output_name') or 'out') + ('' if (b.get('output_name') or '').endswith('.docx') else '.docx'))
    doc.save(out); return send_file(out, as_attachment=True, download_name=os.path.basename(out))

@app.post('/generate/pdf')
def gen_pdf():
    b=request.get_json(force=True) or {}
    tid=b.get('template_id'); vals=b.get('values',{})
    p=os.path.join('templates', tid or '')
    if not p.endswith('.html') or not os.path.exists(p): return jsonify({'ok':False,'error':'template not found'}),404
    html=Template(open(p,'r',encoding='utf-8').read()).render(**vals)
    out=os.path.join(tempfile.gettempdir(), (b.get('output_name') or 'out') + ('' if (b.get('output_name') or '').endswith('.pdf') else '.pdf'))
    HTML(string=html).write_pdf(out); return send_file(out, as_attachment=True, download_name=os.path.basename(out))
