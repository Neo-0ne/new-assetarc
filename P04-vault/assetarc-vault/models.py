
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL=os.getenv('VAULT_DB_URL','sqlite:///assetarc_vault.db')
_engine=create_engine(DB_URL, future=True)
Session=sessionmaker(bind=_engine, expire_on_commit=False)

def init_db():
    with _engine.begin() as c:
        c.execute(text('''CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_email TEXT NOT NULL,
            label TEXT,
            folder TEXT,
            s3_key TEXT NOT NULL,
            s3_preview_key TEXT,
            sha256 TEXT,
            content_type TEXT,
            size_bytes INTEGER,
            approved INTEGER NOT NULL DEFAULT 0,
            version INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )'''))
        c.execute(text('''CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            email TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip TEXT
        )'''))
