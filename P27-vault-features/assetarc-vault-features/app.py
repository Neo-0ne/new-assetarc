
import os, io, time, hashlib
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import boto3
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
app=Flask(__name__); CORS(app)
s3=boto3.client('s3',
    region_name=os.getenv('S3_REGION','af-south-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    endpoint_url=os.getenv('S3_ENDPOINT') or None
)
BUCKET=os.getenv('S3_BUCKET','assetarc-vault')
TTL=int(os.getenv('SIGNED_TTL_SEC','900'))

@app.get('/healthz')
def h(): return jsonify({'ok':True})

@app.get('/presign')
def presign():
    key=request.args.get('key'); method=request.args.get('method','get_object')
    if not key: return jsonify({'ok':False,'error':'key required'}),400
    url=s3.generate_presigned_url(ClientMethod=method, Params={'Bucket':BUCKET,'Key':key}, ExpiresIn=TTL)
    return jsonify({'ok':True,'url':url,'expires_in':TTL})

@app.get('/preview/watermark')
def preview_wm():
    # basic watermark for PNG/JPG previews stored in S3
    key=request.args.get('key'); text=request.args.get('text','ASSETARC')
    if not key: return jsonify({'ok':False,'error':'key required'}),400
    obj=s3.get_object(Bucket=BUCKET, Key=key)
    img=Image.open(io.BytesIO(obj['Body'].read())).convert('RGBA')
    overlay=Image.new('RGBA', img.size, (255,255,255,0))
    draw=ImageDraw.Draw(overlay)
    # Simple diagonal watermark
    w,h=img.size; msg=text
    draw.text((w*0.1,h*0.45), msg, fill=(255,255,255,90))
    out=Image.alpha_composite(img, overlay).convert('RGB')
    buf=io.BytesIO(); out.save(buf, format='JPEG', quality=85); buf.seek(0)
    return send_file(buf, mimetype='image/jpeg', as_attachment=False)
if __name__=='__main__':
    app.run(host='0.0.0.0', port=8027, debug=True)
