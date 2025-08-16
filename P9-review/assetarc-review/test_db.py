import os
import csv
from pathlib import Path

import db


def test_export_csv_empty_rows(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        db.init_db()
        path = db.export_csv('flags', [])
        assert Path(path).exists()
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            assert list(reader) == []
    finally:
        os.chdir(cwd)

