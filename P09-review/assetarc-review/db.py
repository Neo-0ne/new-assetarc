
import os, csv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL=os.getenv('REVIEW_DB_URL','sqlite:///assetarc_review.db')
_engine=create_engine(DB_URL, future=True)
Session=sessionmaker(bind=_engine, expire_on_commit=False)

def init_db():
    with _engine.begin() as c:
        c.execute(text('''CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            type TEXT,
            title TEXT,
            data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )'''))
        c.execute(text('''CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            level TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )'''))

def export_csv(table: str, rows: list[dict]):
    os.makedirs('exports', exist_ok=True)
    path = f'exports/{table}.csv'

    # When there are no rows, ensure we either create an empty CSV with
    # headers or simply return without attempting to access ``rows[0]``.
    if not rows:
        if not os.path.exists(path):
            with _engine.connect() as c:
                result = c.execute(text(f'SELECT * FROM {table} LIMIT 0'))
                fieldnames = result.keys()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=fieldnames).writeheader()
        return path

    new = not os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    return path
