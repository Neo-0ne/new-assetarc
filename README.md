# AssetArc – Integrated Deploy (Flattened)

This package contains **all services (P01–P41)** in a single, flattened tree under `services/`, plus a generator that builds a `docker-compose.integrated.yml` to run the stack locally or on a host.

## Quick Start
1. Install Docker & Docker Compose v2.
2. Copy `.env.global.example` to `.env.global` and fill shared values (domain, JWT secret, AWS keys).
3. Run the compose generator:
   ```bash
   python3 scripts/gen-compose.py
   ```
   This creates `docker-compose.integrated.yml` by scanning service folders and default ports.
4. Boot the stack:
   ```bash
   docker compose -f docker-compose.integrated.yml up -d --build
   ```
5. Open the Admin dashboard (P11) on its mapped port to see service health.

## Notes
- Each service keeps its own `.env.example`. The generator will create `.env.<service>` if missing.
- Reverse proxy (nginx) samples for subdomains are under `reverse-proxy/`. You can deploy them on a gateway host or bake into an Nginx container.
- A **Deployment Checklist (PDF)** is provided at the root, and **UAT script** under `uat-script.md`.
- **infra-bootstrap.zip** contains Terraform starters for S3 bucket (Vault), CloudFront, and IAM policies.
