
import os, boto3, hashlib, datetime

AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY')
S3_REGION=os.getenv('S3_REGION','af-south-1')
S3_BUCKET=os.getenv('S3_BUCKET','assetarc-vault')
S3_ENDPOINT=os.getenv('S3_ENDPOINT') or None
PREFIX_PATTERN=os.getenv('VAULT_PREFIX_PATTERN','{email}/{yyyy}/{mm}/')

def _s3():
    return boto3.client('s3',
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT
    )

def make_key(email:str, filename:str)->str:
    now=datetime.datetime.utcnow()
    key=PREFIX_PATTERN.format(email=email, yyyy=now.strftime('%Y'), mm=now.strftime('%m'))
    return key + filename

def upload_file(path:str, email:str, template_id:str)->str:
    s3=_s3()
    with open(path,'rb') as f:
        data=f.read()
    sha=hashlib.sha256(data).hexdigest()
    name=os.path.basename(path)
    key=make_key(email, name)
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=data,
        ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' if name.endswith('.docx') else 'application/pdf',
        Metadata={
            'docgen':'true',
            'template-id': template_id,
            'sha256': sha
        }
    )
    return key
