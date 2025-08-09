
# AssetArc – Legal Health Check / Risk Exposure Diagnostic (P34)
Periodic audit with risk flags and a printable checklist.

## Quickstart
1) `cp .env.example .env`
2) `pip install -r requirements.txt`
3) `flask --app app.py run --host 0.0.0.0 --port 8034 --debug`

## Endpoints
- `GET  /healthz`
- `GET  /templates` – list bundled templates
- `POST /generate/docx` – `{template_id, values, output_name}`
- `POST /generate/pdf`  – `{template_id, values, output_name}`
