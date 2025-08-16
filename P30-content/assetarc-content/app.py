
import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__); CORS(app)
LLM=os.getenv('LLM_BASE','http://localhost:5002')

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/repurpose')
def repurpose():
    body=request.get_json(force=True) or {}
    content=body.get('content','')
    r=requests.post(LLM.rstrip('/')+'/llm/generate', json={
        'mode':'skill','skill_id':'content_repurpose','vars':{'content':content}
    }, timeout=60)
    return jsonify({'ok':True,'result': r.json()})
