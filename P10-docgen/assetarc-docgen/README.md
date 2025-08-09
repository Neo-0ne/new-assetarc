
# AssetArc – Document Generation Engine (P10 v1.1)

Fully copy‑pasteable service to generate DOCX/PDF outputs, with optional **entitlement check** before final rendering, **Vault alignment** (S3 prefixes), and **Review‑Flag ping** to the Review Queue (P9).

## Endpoints
- `GET  /healthz`
- `GET  /templates` – list available docx/html templates
- `POST /generate/docx` – `{template_id, values, output_name, consume_token?}`
- `POST /generate/pdf`  – `{template_id, values, output_name, consume_token?}`
- `POST /approve-upload` – same body + uploads final to S3 using Vault prefixes
- `POST /flag` – `{level, reason, submission_id?}` forwards to Review service (P9)

## Entitlements (optional)
Set `ENTITLEMENT_REQUIRED=True` to block **final** renders unless the user has a credit/token.
- If `TOKENS_BASE` is set: we check `/tokens/balance?email=` and optionally `POST /tokens/consume`.
- If not set: we fall back to a local `credits` table (`POST /credits/grant {email,amount}` to grant).

## Vault alignment
- Direct S3 upload using AWS creds, or call your P4 service if you prefer. This pack writes to S3 directly for simplicity.
- Key pattern is configurable with `VAULT_PREFIX_PATTERN` (default: `{email}/{yyyy}/{mm}/`).
- File metadata includes `x-amz-meta-docgen: true` and `x-amz-meta-template-id`.

## Quickstart
1) `cp .env.example .env` and fill values.
2) `pip install -r requirements.txt`
3) `python -c "from db import init_db; init_db()"`
4) `flask --app app.py run --host 0.0.0.0 --port 5010 --debug`

## Notes
- DOCX: simple `{{PLACEHOLDER}}` replacements in paragraphs & tables (no complex logic). For loops/conditions, render via PDF (Jinja2 → HTML → PDF).
- PDF: WeasyPrint renders HTML templates with Jinja2 variables; requires system libs (see Dockerfile).
