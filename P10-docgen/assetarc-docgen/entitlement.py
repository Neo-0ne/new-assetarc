
import os, requests
from sqlalchemy import text
from db import Session

TOK_BASE=os.getenv('TOKENS_BASE','').strip()
TOK_KEY=os.getenv('TOKENS_INTERNAL_KEY','').strip()

def has_access(email: str) -> bool:
    if TOK_BASE:
        try:
            r=requests.get(TOK_BASE.rstrip('/')+f'/tokens/balance?email={email}', headers={'Authorization':f'Bearer {TOK_KEY}'}, timeout=6)
            if r.status_code==200 and int(r.json().get('balance',0))>0:
                return True
            return False
        except Exception:
            return False
    # fallback local credits
    s=Session()
    row=s.execute(text('SELECT amount FROM credits WHERE email=:e'),{'e':email}).fetchone()
    return bool(row and int(row[0])>0)

def consume(email: str, amount: int=1, reason: str='docgen_final') -> bool:
    if TOK_BASE:
        try:
            r=requests.post(TOK_BASE.rstrip('/')+'/tokens/consume', headers={'Authorization':f'Bearer {TOK_KEY}','Content-Type':'application/json'}, json={'email':email,'amount':amount,'reason':reason}, timeout=6)
            return r.status_code==200 and r.json().get('ok',False)
        except Exception:
            return False
    s=Session()
    row=s.execute(text('SELECT amount FROM credits WHERE email=:e'),{'e':email}).fetchone()
    if row and int(row[0])>=amount:
        s.execute(text('UPDATE credits SET amount=amount-:a, updated_at=CURRENT_TIMESTAMP WHERE email=:e'),{'a':amount,'e':email}); s.commit(); return True
    return False

def grant(email: str, amount:int=1):
    s=Session()
    row=s.execute(text('SELECT amount FROM credits WHERE email=:e'),{'e':email}).fetchone()
    if row:
        s.execute(text('UPDATE credits SET amount=amount+:a, updated_at=CURRENT_TIMESTAMP WHERE email=:e'),{'a':amount,'e':email})
    else:
        s.execute(text('INSERT INTO credits(email,amount) VALUES (:e,:a)'),{'e':email,'a':amount})
    s.commit()
