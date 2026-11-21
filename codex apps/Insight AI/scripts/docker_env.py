"""Generate local Compose secrets once, without printing them."""
import secrets
from pathlib import Path

path = Path(".env")
if path.exists():
    raise SystemExit(".env exists; preserved. Add missing configuration manually.")
path.write_text("\n".join(f"{key}={secrets.token_hex(24)}" for key in ["POSTGRES_PASSWORD", "DEMO_DB_PASSWORD", "DEMO_CONTROL_TOKEN"]) + "\n")
path.chmod(0o600)
print("Generated .env for local Compose. Values have not been printed.")
