"""Generate a unique local credential without writing secrets to logs."""

import secrets

from sqlalchemy import select

from packages.connectors.replay import snapshot
from services.api.auth import passwords
from services.api.db import DATA, Incident, Session, Setting, User


def setup():
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config("alembic.ini"), "head")
    with Session() as db:
        admin = db.scalar(select(User).where(User.username == "admin"))
        if not admin:
            password = secrets.token_urlsafe(24)
            admin = User(username="admin", password_hash=passwords.hash(password), role="administrator")
            db.add(admin)
            db.flush()
            credential = DATA / "admin-password.txt"
            credential.write_text(password, encoding="utf-8")
            credential.chmod(0o600)
        if not db.get(Setting, "seed-v1"):
            for title, family, severity in [
                ("Checkout latency exceeds the payment deadline", "payment_delay", "P1"),
                ("Elevated connection wait in checkout", "pool_exhaustion", "P2"),
                ("Intermittent errors with incomplete trace coverage", "missing_evidence", "P2"),
            ]:
                db.add(
                    Incident(
                        title=title,
                        severity=severity,
                        mode="replay",
                        created_by=admin.id,
                        description="Seeded replay incident using synthetic telemetry-v1 fixtures.",
                        snapshot=snapshot(family),
                    )
                )
            db.add(Setting(id="seed-v1", data={"version": 1}))
        if not db.get(Setting, "demo"):
            db.add(
                Setting(
                    id="demo",
                    data={"mode": "replay", "fault": None, "revision": 0, "traffic": False, "samples": 0},
                )
            )
        db.commit()
    print(
        "ProductionLens ready. Username: admin. Read the generated password from .productionlens/admin-password.txt. No universal default credential."
    )


if __name__ == "__main__":
    setup()
