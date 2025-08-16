
import os, io
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import text as sql
from auth_middleware import require_auth
from models import init_db, Session
from s3_utils import put_object, presign_get, calc_sha256
from watermark import watermark_image, watermark_pdf

load_dotenv()
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)

@app.before_first_request
def _init(): init_db()

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/files')
@require_auth
def list_files():
    s=Session()
    email=(getattr(request,'user',{}) or {}).get('sub')
    rows=s.execute(sql('SELECT id,label,folder,s3_key,s3_preview_key,approved,version,created_at FROM files WHERE owner_email=:e ORDER BY id DESC'), {'e': email}).all()
    out=[{'id':r[0],'label':r[1],'folder':r[2],'key':r[3],'preview_key':r[4],'approved':bool(r[5]),'version':r[6],'created_at':r[7].isoformat()+'Z'} for r in rows]
    return jsonify({'ok':True,'files':out})

@app.post('/files/upload')
@require_auth
def upload():
    if 'file' not in request.files: return jsonify({'ok':False,'error':'No file'}),400
    f=request.files['file']
    label=request.form.get('label') or f.filename
    folder=request.form.get('folder') or 'uploads'
    email=(getattr(request,'user',{}) or {}).get('sub','client@example.com')
    # compute digest
    data=f.read()
    sha=calc_sha256(io.BytesIO(data))
    content_type=f.mimetype or 'application/octet-stream'
    key=f"{email}/{folder}/{int(datetime.utcnow().timestamp())}_{f.filename}"
    put_object(key, data, content_type)
    s=Session()
    s.execute(sql('INSERT INTO files(owner_email,label,folder,s3_key,sha256,content_type,size_bytes,approved,version) VALUES (:e,:l,:folder,:k,:sha,:ct,:sz,0,1)'),
              {'e':email,'l':label,'folder':folder,'k':key,'sha':sha,'ct':content_type,'sz':len(data)})
    s.commit()
    file_id=s.execute(sql('SELECT last_insert_rowid()')).scalar()
    return jsonify({'ok':True,'id':file_id,'key':key})

@app.get('/files/<int:file_id>')
@require_auth
def meta(file_id):
    s=Session()
    r=s.execute(sql('SELECT id,owner_email,label,folder,s3_key,s3_preview_key,approved,version,content_type,size_bytes,created_at FROM files WHERE id=:i'), {'i':file_id}).fetchone()
    if not r: return jsonify({'ok':False,'error':'Not found'}),404
    email=(getattr(request,'user',{}) or {}).get('sub')
    if r[1]!=email: return jsonify({'ok':False,'error':'Forbidden'}),403
    return jsonify({'ok':True,'file':{'id':r[0],'label':r[2],'folder':r[3],'key':r[4],'preview_key':r[5],'approved':bool(r[6]),'version':r[7],'content_type':r[8],'size_bytes':r[9],'created_at':r[10].isoformat()+'Z'}})

class Disp(BaseModel):
    disposition: str | None = "attachment"
    filename: str | None = None

@app.post('/files/<int:file_id>/signed-url')
@require_auth
def signed(file_id):
    s=Session()
    r=s.execute(sql('SELECT owner_email,s3_key,label,approved FROM files WHERE id=:i'), {'i':file_id}).fetchone()
    if not r: return jsonify({'ok':False,'error':'Not found'}),404
    email=(getattr(request,'user',{}) or {}).get('sub')
    if r[0]!=email: return jsonify({'ok':False,'error':'Forbidden'}),403
    # only allow original if approved; else return preview if exists
    if not r[3]:
        prev=s.execute(sql('SELECT s3_preview_key FROM files WHERE id=:i'), {'i':file_id}).scalar()
        if prev: 
            body=request.get_json(silent=True) or {}
            try: b=Disp(**body)
            except Exception: b=Disp()
            url=presign_get(prev, b.disposition or 'inline', b.filename or r[2])
            return jsonify({'ok':True,'url':url,'preview':True})
        return jsonify({'ok':False,'error':'Not approved; no preview yet'}),403
    body=request.get_json(silent=True) or {}
    try: b=Disp(**body)
    except Exception: b=Disp()
    url=presign_get(r[1], b.disposition or 'attachment', b.filename or r[2])
    return jsonify({'ok':True,'url':url,'preview':False})

@app.post('/files/<int:file_id>/watermark')
@require_auth
def wm(file_id):
    s=Session()
    r=s.execute(sql('SELECT owner_email,s3_key,content_type,label FROM files WHERE id=:i'), {'i':file_id}).fetchone()
    if not r: return jsonify({'ok':False,'error':'Not found'}),404
    email=(getattr(request,'user',{}) or {}).get('sub')
    if r[0]!=email: return jsonify({'ok':False,'error':'Forbidden'}),403
    # download original
    from s3_utils import s3_client, BUCKET
    s3=s3_client()
    obj=s3.get_object(Bucket=BUCKET(), Key=r[1])
    raw=obj['Body'].read()
    overlay=f"{r[3]} – {email} – PREVIEW"
    preview_bytes=None
    if (r[2] or '').lower().startswith('image/'):
        preview_bytes=watermark_image(raw, overlay)
        prev_key=r[1]+".preview.jpg"
        s3.put_object(Bucket=BUCKET(), Key=prev_key, Body=preview_bytes, ContentType='image/jpeg')
    else:
        try:
            preview_bytes=watermark_pdf(raw, overlay)
            prev_key=r[1]+".preview.pdf"
            s3.put_object(Bucket=BUCKET(), Key=prev_key, Body=preview_bytes, ContentType='application/pdf')
        except Exception:
            preview_bytes=watermark_image(raw, overlay)
            prev_key=r[1]+".preview.jpg"
            s3.put_object(Bucket=BUCKET(), Key=prev_key, Body=preview_bytes, ContentType='image/jpeg')
    s.execute(sql('UPDATE files SET s3_preview_key=:k WHERE id=:i'), {'k':prev_key,'i':file_id})
    s.commit()
    return jsonify({'ok':True,'preview_key':prev_key})

@app.post('/files/<int:file_id>/approve')
@require_auth
def approve(file_id):
    s=Session()
    email=(getattr(request,'user',{}) or {}).get('sub')
    # For now, allow owner to approve their own; later restrict to advisors/owner_admin
    s.execute(sql('UPDATE files SET approved=1 WHERE id=:i AND owner_email=:e'), {'i':file_id,'e':email})
    s.commit()
    return jsonify({'ok':True})

@app.post('/files/<int:file_id>/track-download')
@require_auth
def track(file_id):
    s=Session()
    email=(getattr(request,'user',{}) or {}).get('sub')
    ip=request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    s.execute(sql('INSERT INTO downloads(file_id,email,ip) VALUES (:i,:e,:ip)'), {'i':file_id,'e':email,'ip':ip})
    s.commit()
    return jsonify({'ok':True})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5014')), debug=os.getenv('FLASK_ENV')=='development')
