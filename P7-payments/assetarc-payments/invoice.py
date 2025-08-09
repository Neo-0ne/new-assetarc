
import os, datetime, hashlib, boto3
from jinja2 import Template
from weasyprint import HTML

INVOICE_PREFIX=os.getenv('INVOICE_PREFIX','invoices/{email}/{yyyy}/{mm}/')
S3_BUCKET=os.getenv('S3_BUCKET','assetarc-vault')
S3_REGION=os.getenv('S3_REGION','af-south-1')
S3_ENDPOINT=os.getenv('S3_ENDPOINT') or None

def render_invoice_pdf(values: dict, html_template_path: str, out_path: str):
    with open(html_template_path,'r',encoding='utf-8') as f:
        html = Template(f.read()).render(**values)
    HTML(string=html).write_pdf(out_path)

def upload_invoice(path:str, email:str):
    if not os.getenv('AWS_ACCESS_KEY_ID'): return None
    cli=boto3.client('s3', region_name=S3_REGION,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        endpoint_url=S3_ENDPOINT)
    with open(path,'rb') as f: data=f.read()
    key=INVOICE_PREFIX.format(email=email, yyyy=datetime.datetime.utcnow().strftime('%Y'), mm=datetime.datetime.utcnow().strftime('%m')) + os.path.basename(path)
    cli.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType='application/pdf',
                   Metadata={'sha256': hashlib.sha256(data).hexdigest(), 'doc':'invoice'})
    return key
