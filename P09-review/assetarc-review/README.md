
# AssetArc – Notion Sync & Review Queue (P09)

Ingests client submissions, syncs them to **Notion** (if configured), and exposes a **human review queue** with flags.
If Notion isn't configured yet, it uses **SQLite** and also writes **CSV backups** you can open in Excel.

## Endpoints
- `GET  /healthz`
- `POST /submissions` – create a submission `{type, title, data}`
- `GET  /submissions` – list recent submissions (filters: `type`, `email`)
- `POST /flags` – add a review flag `{submission_id, level, reason}`
- `GET  /flags` – list flags (filters: `level`, `status`)
- `POST /flags/<id>/resolve` – mark a flag resolved
- `POST /sync/notion` – re-sync latest items to Notion (admin)

Auth: same JWT as Project 1.

### Fallback behavior
- If `NOTION_TOKEN` or `NOTION_DB_SUBMISSIONS` missing, the service will:
  - Store to SQLite (`assetarc_review.db`)
  - Append rows to `./exports/submissions.csv` and `./exports/flags.csv`

### Quickstart
1. `cp .env.example .env` and fill values (leave Notion empty to use fallback)
2. `pip install -r requirements.txt`
3. `python -c "from db import init_db; init_db()"`
4. `flask --app app.py run --host 0.0.0.0 --port 5016 --debug`
