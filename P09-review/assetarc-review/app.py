
import os, json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import text as sql
from pydantic import BaseModel, ValidationError

from auth_middleware import require_auth
from db import init_db, Session, export_csv
from notion_sync import push_submission, push_flag

load_dotenv()
app=Flask(__name__)
CORS(app, resources={r"/*":{"origins":[o.strip() for o in os.getenv('CORS_ALLOWED_ORIGINS','').split(',') if o.strip()]}},
     supports_credentials=True)

@app.before_first_request
def _init(): init_db()

@app.get('/healthz')
def h(): return jsonify({'ok':True})

class NewSubmission(BaseModel):
    type: str
    title: str
    data: dict

@app.post('/submissions')
@require_auth
def create_submission():
    try:
        body=NewSubmission(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({'ok':False,'error':e.errors()}),400
    s=Session()
    email=(getattr(request,'user',{}) or {}).get('sub','client@example.com')
    s.execute(sql('INSERT INTO submissions(email,type,title,data) VALUES (:e,:t,:ti,:d)'),
              {'e':email,'t':body.type,'ti':body.title,'d':json.dumps(body.data)})
    s.commit()
    sub_id=s.execute(sql('SELECT last_insert_rowid()')).scalar()
    # load row for sync
    row=s.execute(sql('SELECT id,email,type,title,created_at FROM submissions WHERE id=:i'),{'i':sub_id}).fetchone()
    sub={'id':row[0],'email':row[1],'type':row[2],'title':row[3],'created_at':row[4].isoformat()+'Z'}
    push_submission(sub)  # if configured
    export_csv('submissions', [sub])
    return jsonify({'ok':True,'id':sub_id})

@app.get('/submissions')
@require_auth
def list_submissions():
    s=Session()
    q='SELECT id,email,type,title,created_at FROM submissions WHERE 1=1'
    params={}
    t=request.args.get('type'); em=request.args.get('email')
    if t: q+=' AND type=:t'; params['t']=t
    if em: q+=' AND email=:e'; params['e']=em
    q+=' ORDER BY id DESC LIMIT 200'
    rows=s.execute(sql(q), params).all()
    out=[{'id':r[0],'email':r[1],'type':r[2],'title':r[3],'created_at':r[4].isoformat()+'Z'} for r in rows]
    return jsonify({'ok':True,'items':out})

class NewFlag(BaseModel):
    submission_id: int
    level: str
    reason: str

@app.post('/flags')
@require_auth
def add_flag():
    try:
        body=NewFlag(**request.get_json(force=True))
    except ValidationError as e:
        return jsonify({'ok':False,'error':e.errors()}),400
    s=Session()
    s.execute(sql('INSERT INTO flags(submission_id,level,reason,status) VALUES (:sid,:lvl,:rsn,"open")'),
              {'sid':body.submission_id,'lvl':body.level,'rsn':body.reason})
    s.commit()
    fid=s.execute(sql('SELECT last_insert_rowid()')).scalar()
    flag={'id':fid,'submission_id':body.submission_id,'level':body.level,'reason':body.reason,'status':'open'}
    push_flag(flag)  # if configured
    export_csv('flags', [flag])
    return jsonify({'ok':True,'id':fid})

@app.get('/flags')
@require_auth
def list_flags():
    s=Session()
    q='SELECT id,submission_id,level,reason,status,created_at,resolved_at FROM flags WHERE 1=1'
    params={}
    lvl=request.args.get('level'); st=request.args.get('status')
    if lvl: q+=' AND level=:l'; params['l']=lvl
    if st: q+=' AND status=:s'; params['s']=st
    q+=' ORDER BY id DESC LIMIT 200'
    rows=s.execute(sql(q), params).all()
    out=[{'id':r[0],'submission_id':r[1],'level':r[2],'reason':r[3],'status':r[4],
          'created_at':(r[5].isoformat()+'Z') if r[5] else None,
          'resolved_at':(r[6].isoformat()+'Z') if r[6] else None} for r in rows]
    return jsonify({'ok':True,'items':out})

@app.post('/flags/<int:fid>/resolve')
@require_auth
def resolve_flag(fid):
    s=Session()
    s.execute(sql('UPDATE flags SET status="resolved", resolved_at=CURRENT_TIMESTAMP WHERE id=:i'), {'i':fid})
    s.commit()
    return jsonify({'ok':True})

@app.post('/sync/notion')
@require_auth
def manual_sync():
    # Placeholder: with CSV fallback, on-demand pushing is handled on creation.
    return jsonify({'ok':True,'message':'Items are pushed to Notion on create if configured; CSV fallback is continuous.'})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5016')), debug=os.getenv('FLASK_ENV')=='development')
