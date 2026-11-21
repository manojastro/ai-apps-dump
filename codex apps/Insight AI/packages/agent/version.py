import os
import subprocess
from pathlib import Path

from packages.agent.contracts import action_hash
from packages.connectors.replay import TOOLS


def version_metadata(method):
    try:
        commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=2)
            .decode()
            .strip()
        )
    except (subprocess.SubprocessError, OSError):
        commit = "uncommitted-workspace"
    return {
        "contract": "agent-v1",
        "method": method,
        "git_commit": commit,
        "prompt_hash": action_hash(
            {
                "prompt": Path(
                    "packages/agent/scripted.py" if method.startswith("script") else "packages/agent/live.py"
                ).read_text()
            }
        ),
        "tool_schema_hash": action_hash(TOOLS),
        "model": "scripted" if method.startswith("script") else os.environ.get("MODEL_ID", "unconfigured"),
        "generation": {"temperature": 0},
        "runtime": {"tool_limit": 12, "model_limit": 8},
        "dependency_lock_hash": action_hash({"lock": Path("uv.lock").read_text()}),
    }
