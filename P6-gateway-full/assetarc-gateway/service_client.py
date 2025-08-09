
import os, requests
from flask import request, Response

def _copy_headers(resp):
    headers = {}
    for k,v in resp.headers.items():
        # do not forward hop-by-hop headers
        if k.lower() in ('content-encoding','transfer-encoding','connection'):
            continue
        headers[k] = v
    return headers

def forward_json(base_url: str, method: str, path: str, json_body=None, timeout=20):
    url = base_url.rstrip('/') + path
    # forward cookies (session)
    cookies = request.cookies
    headers = {'Content-Type':'application/json'}
    auth = request.headers.get('Authorization')
    if auth: headers['Authorization'] = auth
    r = requests.request(method.upper(), url, json=json_body, headers=headers, cookies=cookies, timeout=timeout)
    return Response(r.content, status=r.status_code, headers=_copy_headers(r))
