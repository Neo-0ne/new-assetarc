#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Service folders may live directly under the repo root in some distributions
# or inside a dedicated "services" directory.  Fall back to the root if the
# "services" folder is missing so the generator still works.
SERVICES = ROOT / "services"
if not SERVICES.exists():
    SERVICES = ROOT

OUT = ROOT / "docker-compose.integrated.yml"
GLOBAL_ENV = ROOT / ".env.global"

# Default ports for known services (override by .env.example PORT or hard-coded app.py)
default_ports = {
  "assetarc-auth": 5001,
  "assetarc-llm": 5002,
  "assetarc-fx": 5003,
  "assetarc-doc-engine": 5014,
  "assetarc-admin": 5011,
  "assetarc-analytics": 5012,
  "assetarc-review": 5016,
  "assetarc-subscriptions": 5017,
  "assetarc-vault-features": 8027,
  "assetarc-leadmagnet": 8029,
  "assetarc-content": 8030,
  "assetarc-education": 8031,
  "assetarc-marketing-automation": 8032,
  "assetarc-filemgmt": 8033,
  "assetarc-legal-healthcheck": 8034,
  "assetarc-doc-annotation": 8035,
  "assetarc-advisor-kpi": 8036,
  "assetarc-submission-checker": 8037,
  "assetarc-bbbee": 8038,
  "assetarc-trustee-services": 8039,
  "assetarc-newsletter-logic": 8040,
  "assetarc-utm-metrics": 8041
}

def sniff_service_root(pdir: Path):
    # find the code root folder (one that contains app.py / requirements.txt)
    candidates = []
    for sub in pdir.iterdir():
        if sub.is_dir() and (sub / "app.py").exists() and (sub / "requirements.txt").exists():
            candidates.append(sub)
    if candidates:
        # Prefer folder names starting with assetarc-
        for c in candidates:
            if c.name.startswith("assetarc-"):
                return c
        return candidates[0]
    return None

def derive_port(service_root: Path):
    # Try .env.example's PORT, otherwise default table.
    envex = service_root / ".env.example"
    if envex.exists():
        for line in envex.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("PORT="):
                try:
                    return int(line.strip().split("=",1)[1])
                except Exception:
                    pass
    return default_ports.get(service_root.name, None)

def load_global_env():
    out = {}
    if (GLOBAL_ENV).exists():
        for line in GLOBAL_ENV.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v = line.split("=",1)
            out[k.strip()] = v.strip()
    return out

def upsert_envfile(target: Path, inject: dict):
    lines = []
    existing = {}
    if target.exists():
        for line in target.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k,v = line.split("=",1); existing[k]=v
            lines.append(line)
    for k,v in inject.items():
        if k in existing: continue
        lines.append(f"{k}={v}")
    target.write_text("\n".join(lines)+("\n" if lines and not lines[-1].endswith("\n") else ""), encoding="utf-8")

def main():
    globs = load_global_env()
    services = {}
    for p in sorted(SERVICES.iterdir(), key=lambda p: p.name):
        if not p.is_dir():
            continue
        sroot = sniff_service_root(p)
        if not sroot:
            continue
        port = derive_port(sroot)
        name = sroot.name.replace("assetarc-", "")
        envfile = sroot / ".env"
        # inject shared vars (non-destructive)
        inject = {}
        for k in (
            "JWT_SECRET",
            "COOKIE_DOMAIN",
            "COOKIE_SECURE",
            "CORS_ALLOWED_ORIGINS",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "S3_REGION",
            "S3_BUCKET",
            "SES_REGION",
            "SES_FROM_EMAIL",
            "OPENAI_API_KEY",
            "DEFAULT_MODEL",
            "YOCO_SECRET_KEY",
            "NOWPAYMENTS_API_KEY",
            "CALENDLY_ORG_URI",
            "GOOGLE_SERVICE_ACCOUNT_JSON_PATH",
        ):
            if k in globs:
                inject[k] = globs[k]
        upsert_envfile(envfile, inject)

        services[name] = {
            "build": {"context": str(sroot)},
            "container_name": f"assetarc-{name}",
            "env_file": [str(envfile)],
            "restart": "unless-stopped",
        }
        if port:
            services[name]["ports"] = [f"{port}:{port}"]

    compose = {"version": "3.9", "services": services}
    OUT.write_text(yaml.safe_dump(compose, sort_keys=True), encoding="utf-8")
    print(f"Wrote {OUT} with {len(services)} services.")

if __name__ == "__main__":
    try:
        import yaml  # type: ignore
    except Exception:
        print(
            "ERROR: PyYAML not available in your host Python. Install with: pip install pyyaml"
        )
        sys.exit(1)
    main()
