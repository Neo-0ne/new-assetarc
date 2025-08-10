#!/usr/bin/env python3
import os, sys, yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
compose_in = ROOT / os.getenv("COMPOSE_FILE", "docker-compose.integrated.yml")
compose_out = ROOT / os.getenv("OUT_FILE", "docker-compose.integrated.yml")

owner = (os.getenv("GHCR_OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER") or "").lower()
if not owner:
    print("ERROR: Set GHCR_OWNER=<org-or-user>.", file=sys.stderr)
    sys.exit(1)

prefix = os.getenv("IMAGE_PREFIX", "assetarc")
tag = os.getenv("IMAGE_TAG", "main")

if not compose_in.exists():
    print(f"ERROR: Compose file not found: {compose_in}", file=sys.stderr)
    sys.exit(1)

data = yaml.safe_load(compose_in.read_text())

services = data.get("services") or {}
for key, svc in services.items():
    # key should match p##-something (lowercase). The builder used the same for image suffix.
    image = f"ghcr.io/{owner}/{prefix}-{key}:{tag}"
    svc["image"] = image
    svc.pop("build", None)

compose_out.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
print(f"[OK] rewrote {compose_out} to use prebuilt images ({tag}).")
