
import os, tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from sqlalchemy import text as sql

from auth_middleware import require_auth
from db import init_db, Session
from entitlement import has_access, consume, grant
from vault_uploader import upload_file
from docx_engine import fill_docx_template
from pdf_engine import render_pdf_from_html_template

load_dotenv()
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)

TEMPLATES_DIR='templates'

@app.before_first_request
def _init(): init_db()

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/templates')
@require_auth
def templates():
    # list docx and html templates with simple IDs
    files=[]
    for name in os.listdir(TEMPLATES_DIR):
        if name.endswith('.docx') or name.endswith('.html'):
            files.append({'id': name, 'kind': 'docx' if name.endswith('.docx') else 'html'})
    return jsonify({'ok':True, 'templates':files})

class DocBody(BaseModel):
    template_id: str
    values: dict
    output_name: str
    consume_token: bool | None = False

def _user_email():
    u=getattr(request,'user',{}) or {}
    return u.get('sub') or u.get('email') or 'client@example.com'

def _need_entitlement(consume_flag: bool) -> bool:
    # Only enforce for "final" renders—/approve-upload path always enforces. For /generate/* we enforce when consume_token==True.
    required = os.getenv('ENTITLEMENT_REQUIRED','True').lower()=='true'
    return required and consume_flag

@app.post('/generate/docx')
@require_auth
def gen_docx():
    try:
        b=DocBody(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({'ok':False,'error':e.errors()}),400
    email=_user_email()
    if _need_entitlement(b.consume_token or False):
        if not has_access(email): return jsonify({'ok':False,'error':'No entitlement'}),402
        if not consume(email,1, os.getenv('CONSUME_REASON','docgen_final')):
            return jsonify({'ok':False,'error':'Failed to consume entitlement'}),402
    tpl=os.path.join(TEMPLATES_DIR,b.template_id)
    if not os.path.exists(tpl) or not tpl.endswith('.docx'):
        return jsonify({'ok':False,'error':'Template not found or not DOCX'}),404
    out=os.path.join(tempfile.gettempdir(), b.output_name if b.output_name.endswith('.docx') else b.output_name+'.docx')
    fill_docx_template(tpl, b.values, out)
    return send_file(out, as_attachment=True, download_name=os.path.basename(out))

@app.post('/generate/pdf')
@require_auth
def gen_pdf():
    try:
        b=DocBody(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({'ok':False,'error':e.errors()}),400
    email=_user_email()
    if _need_entitlement(b.consume_token or False):
        if not has_access(email): return jsonify({'ok':False,'error':'No entitlement'}),402
        if not consume(email,1, os.getenv('CONSUME_REASON','docgen_final')):
            return jsonify({'ok':False,'error':'Failed to consume entitlement'}),402
    tpl=os.path.join(TEMPLATES_DIR,b.template_id)
    if not os.path.exists(tpl) or not tpl.endswith('.html'):
        return jsonify({'ok':False,'error':'Template not found or not HTML'}),404
    out=os.path.join(tempfile.gettempdir(), b.output_name if b.output_name.endswith('.pdf') else b.output_name+'.pdf')
    render_pdf_from_html_template(tpl, b.values, out)
    return send_file(out, as_attachment=True, download_name=os.path.basename(out))

class ApproveBody(BaseModel):
    template_id: str
    values: dict
    output_name: str
    kind: str  # 'docx' or 'pdf'

@app.post('/approve-upload')
@require_auth
def approve_upload():
    try:
        b=ApproveBody(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({'ok':False,'error':e.errors()}),400
    email=_user_email()
    # enforce entitlement here always
    if os.getenv('ENTITLEMENT_REQUIRED','True').lower()=='true':
        if not has_access(email): return jsonify({'ok':False,'error':'No entitlement'}),402
        if not consume(email,1, os.getenv('CONSUME_REASON','docgen_final')):
            return jsonify({'ok':False,'error':'Failed to consume entitlement'}),402
    tpl=os.path.join(TEMPLATES_DIR,b.template_id)
    if not os.path.exists(tpl):
        return jsonify({'ok':False,'error':'Template not found'}),404
    import tempfile
    if b.kind=='docx':
        out=os.path.join(tempfile.gettempdir(), b.output_name if b.output_name.endswith('.docx') else b.output_name+'.docx')
        fill_docx_template(tpl, b.values, out)
    elif b.kind=='pdf':
        out=os.path.join(tempfile.gettempdir(), b.output_name if b.output_name.endswith('.pdf') else b.output_name+'.pdf')
        render_pdf_from_html_template(tpl, b.values, out)
    else:
        return jsonify({'ok':False,'error':'Unknown kind'}),400
    # upload to S3 Vault
    key=upload_file(out, email, b.template_id)
    s=Session(); s.execute(sql('INSERT INTO renders(email,template_id,kind,output_name,s3_key) VALUES (:e,:t,:k,:o,:s)'),
                           {'e':email,'t':b.template_id,'k':b.kind,'o':os.path.basename(out),'s':key})
    s.commit()
    return jsonify({'ok':True,'s3_key':key})

class FlagBody(BaseModel):
    level: str
    reason: str
    submission_id: int | None = None

@app.post('/flag')
@require_auth
def flag():
    base=os.getenv('REVIEW_BASE','').strip()
    bearer=os.getenv('REVIEW_BEARER','').strip()
    if not base or not bearer:
        return jsonify({'ok':False,'error':'REVIEW_BASE and REVIEW_BEARER required'}),400
    try:
        b=FlagBody(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({'ok':False,'error':e.errors()}),400
    import requests
    headers={'Content-Type':'application/json', 'Authorization': f'Bearer {bearer}'}
    r=requests.post(base.rstrip('/')+'/flags', headers=headers,
                    json={'submission_id': b.submission_id or 0, 'level': b.level, 'reason': b.reason}, timeout=6)
    if r.status_code==200:
        return jsonify({'ok':True})
    return jsonify({'ok':False,'status':r.status_code,'resp': r.text}),502

@app.post('/credits/grant')
def credits_grant():
    # local fallback helper
    body=request.get_json(force=True) or {}
    email=body.get('email'); amt=int(body.get('amount',1))
    if not email: return jsonify({'ok':False,'error':'email required'}),400
    grant(email, amt)
    return jsonify({'ok':True})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5010')), debug=os.getenv('FLASK_ENV')=='development')
