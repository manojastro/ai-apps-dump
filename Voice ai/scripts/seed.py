"""Seed synthetic data once (idempotent). `python scripts/seed.py` - used as the compose seed step."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select  # noqa: E402

from app.data.db import init_db, session  # noqa: E402
from app.data.models import Patient  # noqa: E402
from app.data.seed import seed  # noqa: E402

if __name__ == "__main__":
    init_db()
    with session() as s:
        have = s.scalar(select(func.count()).select_from(Patient))
    if have:
        print(f"already seeded ({have} patients); nothing to do")
    else:
        print("seeded:", seed())
