
# AssetArc – Payments & Tokenization (Full)

Purpose:
- Create crypto invoices via **NOWPayments**.
- Receive webhooks from **NOWPayments** and **Yoco** (card).
- On confirmed payment, **mint usage tokens** via the Tokens service.
- Enforce "no API use before payment" by gating downstream services on tokens.

## Endpoints
- `GET  /healthz` – health probe
- `POST /payments/create-invoice/nowpayments` – server-side invoice creation
- `POST /webhook/nowpayments` – confirm crypto payments (mints token)
- `POST /webhook/yoco` – confirm card payments (mints token)

## Quickstart
1) `cp .env.example .env` and set keys.
2) `pip install -r requirements.txt`
3) `flask --app app.py run --host 0.0.0.0 --port 5011 --debug`

## Notes
- **Yoco**: this pack processes webhooks. Creating payment links/sessions can be done client- or server-side; integrate your preferred Yoco flow on the frontend. Webhook confirmation here will mint tokens.
- **NOWPayments**: server creates an invoice; user pays the hosted page; IPN hits `/webhook/nowpayments`.
- **Security**: Set `TOKENS_INTERNAL_KEY` to a strong secret, shared with the Tokens service.
