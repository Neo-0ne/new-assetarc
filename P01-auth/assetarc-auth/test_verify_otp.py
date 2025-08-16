import bcrypt
from app import app, eng
from sqlalchemy import text

def test_verify_otp_bad_exp():
    code='123456'
    hashed=bcrypt.hashpw(code.encode(), bcrypt.gensalt())
    with eng.begin() as c:
        c.execute(text('DELETE FROM otps WHERE email=:e'),{'e':'test@example.com'})
        c.execute(text('INSERT INTO otps(email,hash,exp) VALUES (:e,:h,:x)'),
                  {'e':'test@example.com','h':hashed,'x':'invalid'})
    client=app.test_client()
    resp=client.post('/auth/verify-otp', json={'email':'test@example.com','code':code})
    assert resp.status_code==400
