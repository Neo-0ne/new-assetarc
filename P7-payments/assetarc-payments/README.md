
# AssetArc – Payments & Tokenization (P7)

Yoco (card) + NOWPayments (crypto) webhooks, token mint/consume, and invoice/receipt PDF generation.

## Endpoints
- `GET  /healthz`
- `POST /checkout/yoco` – create a Yoco checkout (stub; returns redirect URL placeholder)
- `POST /webhook/yoco` – webhook handler (verifies, then mints tokens and generates invoice)
- `POST /checkout/nowpayments` – create NOWPayments invoice (stub)
- `POST /webhook/nowpayments` – webhook handler for crypto
- `GET  /tokens/balance?email=` – current balance
- `POST /tokens/grant` – admin mint `{email, amount, reason}`
- `POST /tokens/consume` – consume `{email, amount, reason}`

Invoices render from HTML template using WeasyPrint. Receipts can be generated similarly.
