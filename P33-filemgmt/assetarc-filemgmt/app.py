
import os, io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import boto3

load_dotenv()
app=Flask(__name__); CORS(app)
s3=boto3.client('s3',
    region_name=os.getenv('S3_REGION','af-south-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    endpoint_url=os.getenv('S3_ENDPOINT') or None
)
BUCKET=os.getenv('S3_BUCKET','assetarc-vault')

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/list')
def list():
    prefix=request.args.get('prefix','')
    r=s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    items=[{'key':o['Key'],'size':o.get('Size',0)} for o in r.get('Contents',[])]
    return jsonify({'ok':True,'items':items})

@app.post('/upload')
def upload():
    f=request.files.get('file'); prefix=request.form.get('prefix','')
    key=(prefix or '') + f.filename
    s3.put_object(Bucket=BUCKET, Key=key, Body=f.read())
    return jsonify({'ok':True,'key':key})

@app.get('/download')
def download():
    key=request.args.get('key'); obj=s3.get_object(Bucket=BUCKET, Key=key)
    return send_file(io.BytesIO(obj['Body'].read()), as_attachment=True, download_name=key.split('/')[-1])

@app.delete('/delete')
def delete():
    key=request.args.get('key'); s3.delete_object(Bucket=BUCKET, Key=key); return jsonify({'ok':True})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=8033, debug=True)
