
import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()
app=Flask(__name__); CORS(app)

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/fx')
def fx():
    base=request.args.get('base','USD'); target=request.args.get('target','ZAR')
    url=f'https://api.exchangerate.host/latest?base={base}&symbols={target}'
    r=requests.get(url, timeout=10).json()
    rate=r['rates'][target.upper()]
    return jsonify({'ok':True,'base':base.upper(),'target':target.upper(),'rate': rate})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT','5003')), debug=os.getenv('FLASK_ENV')=='development')
