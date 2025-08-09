
# AssetArc – Trustee Services Bot (P39)
Generates minutes, resolutions, and agendas.

## Quickstart
1) `cp .env.example .env`
2) `pip install -r requirements.txt`
3) `flask --app app.py run --host 0.0.0.0 --port 8039 --debug`

## Endpoints
- `GET  /healthz`
- `GET  /templates` – list bundled templates
- `POST /generate/docx` – `{template_id, values, output_name}`
- `POST /generate/pdf`  – `{template_id, values, output_name}`
