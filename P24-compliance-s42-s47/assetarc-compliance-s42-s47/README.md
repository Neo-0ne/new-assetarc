
# AssetArc – Section 42 Roll-over + s47 Compliance Bot (P24)
Produces compliance letters and checklists for s42 roll-over and s47 liquidation.

## Quickstart
1) `cp .env.example .env`
2) `pip install -r requirements.txt`
3) `flask --app app.py run --host 0.0.0.0 --port 8024 --debug`

## Endpoints
- `GET  /healthz`
- `GET  /templates` – list bundled templates
- `POST /generate/docx` – `{template_id, values, output_name}`
- `POST /generate/pdf`  – `{template_id, values, output_name}`
