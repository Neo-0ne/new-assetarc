
import os, boto3, hashlib

def s3_client():
    kw={'region_name': os.getenv('S3_REGION','af-south-1')}
    if os.getenv('S3_ENDPOINT'): kw['endpoint_url']=os.getenv('S3_ENDPOINT')
    return boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), **kw)

BUCKET=lambda: os.getenv('S3_BUCKET','assetarc-vault')
SIGNED_TTL=lambda: int(os.getenv('S3_SIGNED_TTL_SEC','900'))

def put_object(key: str, body, content_type: str):
    s3=s3_client()
    s3.put_object(Bucket=BUCKET(), Key=key, Body=body, ContentType=content_type)

def calc_sha256(fp) -> str:
    h=hashlib.sha256()
    while True:
        chunk=fp.read(8192)
        if not chunk: break
        h.update(chunk)
    fp.seek(0)
    return h.hexdigest()

def presign_get(key: str, disposition='attachment', filename=None):
    s3=s3_client()
    extra={'ResponseContentDisposition': f'{disposition}; filename="{filename or key.split("/")[-1]}"'}
    return s3.generate_presigned_url('get_object', Params={'Bucket':BUCKET(),'Key':key, **extra},
                                     ExpiresIn=SIGNED_TTL())
