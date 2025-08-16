
import os
from typing import Optional
try:
    from notion_client import Client
except Exception:
    Client = None

def _client() -> Optional['Client']:
    token=os.getenv('NOTION_TOKEN')
    if not token or Client is None: return None
    return Client(auth=token)

def push_submission(sub: dict) -> bool:
    cli=_client()
    db=os.getenv('NOTION_DB_SUBMISSIONS')
    if not cli or not db: return False
    props={
        'Title': {'title': [{'text': {'content': sub.get('title','(untitled)')}}]},
        'Email': {'email': sub.get('email')},
        'Type': {'select': {'name': sub.get('type','General')}},
        'Created': {'date': {'start': sub.get('created_at')}},
    }
    cli.pages.create(parent={'database_id': db}, properties=props)
    return True

def push_flag(flag: dict) -> bool:
    cli=_client()
    db=os.getenv('NOTION_DB_FLAGS')
    if not cli or not db: return False
    props={
        'SubmissionID': {'number': flag.get('submission_id')},
        'Level': {'select': {'name': flag.get('level')}},
        'Reason': {'rich_text': [{'text': {'content': flag.get('reason','')}}]},
        'Status': {'select': {'name': flag.get('status','open')}},
    }
    cli.pages.create(parent={'database_id': db}, properties=props)
    return True
