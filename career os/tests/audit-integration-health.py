"""Read-only local Hermes/Telegram health; never print credentials or send messages."""
import json
import logging
import sys
from pathlib import Path
from urllib.request import urlopen

profile = Path(r"C:\Users\manoj\AppData\Local\hermes")
sys.path.insert(0, str(profile / "hermes-agent"))
logging.disable(logging.CRITICAL)
from hermes_cli.config import load_env

env = load_env()
output = {"telegram_token_configured": bool(env.get("TELEGRAM_BOT_TOKEN"))}
try:
    state = json.loads((profile / "gateway_state.json").read_text(encoding="utf-8"))
    output["gateway_state_keys"] = sorted(state.keys())
    output["gateway_pid"] = state.get("pid")
except Exception as error:
    output["gateway_state_error"] = type(error).__name__
token = env.get("TELEGRAM_BOT_TOKEN")
if token:
    try:
        with urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=15) as response:
            body = json.load(response)
            output["telegram_auth_http"] = response.status
            output["telegram_auth_ok"] = body.get("ok", False)
    except Exception as error:
        output["telegram_auth_error_type"] = type(error).__name__
        output["telegram_auth_http"] = getattr(error, "code", None)
print(json.dumps(output))
