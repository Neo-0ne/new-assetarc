
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
DB_URL=os.getenv('BOOK_DB_URL','sqlite:///assetarc_booking.db')
_engine=create_engine(DB_URL, future=True)
Session=sessionmaker(bind=_engine, expire_on_commit=False)
def init_db():
    with _engine.begin() as c:
        c.execute(text('''CREATE TABLE IF NOT EXISTS entitlements (
            email TEXT PRIMARY KEY,
            credits INTEGER NOT NULL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)'''))
        c.execute(text('''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calendly_event TEXT,
            invitee_email TEXT,
            status TEXT,
            payload TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP)'''))
