
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app=Flask(__name__); CORS(app, supports_credentials=True)
client=OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MODEL=os.getenv('DEFAULT_MODEL','gpt-4o-mini')

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.post('/llm/generate')
def gen():
    b=request.get_json(force=True) or {}
    messages=b.get('messages') or [{'role':'user','content':'Say hello.'}]
    m=b.get('model') or MODEL
    r=client.chat.completions.create(model=m, messages=messages, temperature=float(b.get('temperature',0.2)))
    return jsonify({'ok':True,'text': r.choices[0].message.content, 'model':m})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5002')), debug=os.getenv('FLASK_ENV')=='development')
