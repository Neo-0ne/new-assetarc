# Developer Onboarding — AssetArc Integrated Stack (P01–P41)

**Goal**: Keep the full stack running and harden one project (P##) at a time. Open **one PR per project** with evidence. Wait for approval before the next.

## Quick Start
1. Install Docker + Docker Compose v2 and Python 3.11+
2. Copy `.env.global.example` → `.env.global` and fill secrets (JWT, AWS, OpenAI, Yoco, NOWPayments, Calendly/Google).
3. Generate compose:
   ```bash
   python3 scripts/gen-compose.py
   ```
4. Boot everything:
   ```bash
   docker compose -f docker-compose.integrated.yml up -d --build
   ```
5. Run smoke tests from `uat-script.md`.

## Work Order
Core: P01, P02, P03, P14 → Platform: P07, P10, P11, P12, P17, P27 → Client: P13, P15, P18–P26 → Comms: P29, P30, P32, P40, P41 → Optional: P31, P33, P34–P39.

## For Each Project
- Branch `feat/P##-short-slug`
- Change only `services/P##-*` (no contract/port changes without approval)
- Include:
  - `CHANGELOG.md`
  - `TEST-EVIDENCE/` (requests, logs, screenshots)
  - `.env.delta` (any new env vars)
- Open PR titled `P##: <summary>`
- After approval & merge: tag `P##-approved-v1`

## External Services
Use sandbox/test: SES, Yoco, NOWPayments, Calendly, Google. No real keys in commits.

## Guardrails
Do not rename endpoints, ports, cookies, or payload shapes without written approval.

## CI
GitHub Actions builds only **changed** services for each PR. Add tests inside each service as needed.
