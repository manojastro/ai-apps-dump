#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database.session import init_db  # noqa: E402
from app.services.seed import seed_all  # noqa: E402


def main() -> None:
    os.makedirs("/data", exist_ok=True)
    init_db()
    try:
        print(seed_all(force=False))
    except Exception as exc:
        print("seed failed", exc)
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, app_dir=str(ROOT / "backend"))


if __name__ == "__main__":
    main()
