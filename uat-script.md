# AssetArc – UAT Script (Integrated Stack)

## 1. Authentication (P01)
- Open the WP page with [assetarc_login] shortcode.
- Request OTP for tester email; verify; confirm cookies set.
- Call /auth/user via Postman: expect 200 and user payload.

## 2. LLM Layer (P02)
- Hit /skills (auth required): expect list.
- POST /llm/generate (mode=skill: legal_summary) with sample text: expect concise bullets.

## 3. FX & Price Locks (P03)
- GET /fx/latest?base=USD&symbols=ZAR: numeric rate.
- POST /fx/lock {USD->ZAR}: expect lock_id and 24h expiry.

## 4. Document Engine (P14)
- POST /generate/docx using templates/letter.docx + values.
- POST /generate/pdf using templates/report.html + values.

## 5. Payments & Tokens (P07 + P17)
- Simulate payment webhook to P07; expect token minted in P17.
- GET /balance in P17 for the email: tokens_left >= expected.

## 6. Vault Delivery (P27)
- Upload a test file to S3 in the configured bucket.
- GET /presign?key=...: opens file via signed URL.
- GET /preview/watermark?key=...: watermarked JPEG preview.

## 7. Marketing + Newsletter (P32 + P40)
- POST /render.pdf with template vars: returns PDF.
- Open PDF to confirm fonts/render.

## 8. UTM & Analytics (P41 + P12)
- POST /track test events; GET /export.csv shows rows.
- POST /report/pdf in P12 to export analytics summary.

## 9. Admin (P11)
- Open dashboard /status: all services show ✅ UP.

## 10. Booking Flow (P10) (if present)
- Open availability page, confirm slots visible unauthenticated.
- After test payment, booking confirms and iCal sent.

## Pass/Fail
Document any failures with steps and logs.
