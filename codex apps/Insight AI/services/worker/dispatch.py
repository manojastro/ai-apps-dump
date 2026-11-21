"""RQ transport with a database reconciliation loop; DB jobs remain authoritative."""

import os
import subprocess
import sys
import time

from redis import Redis
from rq import Queue
from sqlalchemy import select

from services.api.db import Job, Session, Setting


def main():
    connection = Redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("productionlens", connection=connection)
    worker = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "rq.cli",
            "worker",
            "productionlens",
            "--url",
            os.environ["REDIS_URL"],
            "--worker-class",
            "rq.worker.SimpleWorker",
        ]
    )
    try:
        while worker.poll() is None:
            with Session() as db:
                heartbeat = db.get(Setting, "worker")
                if heartbeat:
                    heartbeat.data = {"at": time.time()}
                else:
                    db.add(Setting(id="worker", data={"at": time.time()}))
                queued = db.scalar(select(Job.id).where(Job.status == "queued").limit(1))
                db.commit()
            try:
                if queued and len(queue) < 2:
                    queue.enqueue("services.worker.runner.work_once", job_timeout=900, result_ttl=60)
            except Exception:
                pass  # DB reconciliation below survives Redis availability loss.
            from services.worker.runner import work_once

            # Reclaim orphaned DB jobs even if their Redis message disappeared.
            work_once()
            time.sleep(1)
    finally:
        worker.terminate()
        worker.wait(timeout=10)


if __name__ == "__main__":
    main()
