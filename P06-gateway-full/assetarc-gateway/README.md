
# AssetArc Gateway (Flask API Bridge)

Single entrypoint that:

- Verifies sessions (shares JWT secret with Auth).
- Proxies/aggregates calls to downstream services (Auth, FX, LLM, Payments, Booking, Vault, Docs).
- Centralizes CORS and cookie handling so web UIs (WordPress/app) only talk to the gateway.

## Endpoints (starter set)

- `GET  /healthz` – health probe
- `GET  /user` – current user (from cookie/JWT)
- `GET  /bridge/fx/latest` – pass-through to FX service
- `POST /bridge/payments/create-invoice/nowpayments` – pass-through to Payments
- `GET  /bridge/booking/availability` – read availability from Booking (if enabled)
- `POST /bridge/llm/generate` – pass-through to LLM layer
- `/bridge/vault/*` – generic pass-through to Vault service
- `/bridge/docs/*` – generic pass-through to Docs service

> Extend `service_client.py` to add more bridges with identical auth/cookie behavior.

## Quickstart

1) `cp .env.example .env` and fill service base URLs + CORS + JWT.
2) `pip install -r requirements.txt`
3) `flask --app app.py run --host 0.0.0.0 --port 5010 --debug`

## Deploy

- Docker (Dockerfile + docker-compose.yml) or systemd + Gunicorn behind Nginx (`nginx/assetarc-gateway.conf`).
