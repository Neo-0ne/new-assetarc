import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv('DOCGEN_DB_URL', 'sqlite:///assetarc_docgen.db')
_engine = create_engine(DB_URL, future=True)
Session = sessionmaker(bind=_engine, expire_on_commit=False)


def init_db():
    with _engine.begin() as c:
        c.execute(text("""CREATE TABLE IF NOT EXISTS credits (
            email TEXT PRIMARY KEY,
            amount INTEGER NOT NULL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""))
        c.execute(text("""CREATE TABLE IF NOT EXISTS renders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            template_id TEXT,
            kind TEXT,
            output_name TEXT,
            s3_key TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""))

