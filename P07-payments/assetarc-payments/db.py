
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
DB_URL=os.getenv('PAY_DB_URL','sqlite:///assetarc_payments.db')
_engine=create_engine(DB_URL, future=True)
Session=sessionmaker(bind=_engine, expire_on_commit=False)
def init_db():
    with _engine.begin() as c:
        c.execute(text('''CREATE TABLE IF NOT EXISTS tokens (
            email TEXT PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)'''))
        c.execute(text('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT, ext_id TEXT, email TEXT, amount REAL, currency TEXT,
            status TEXT, meta TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)'''))
