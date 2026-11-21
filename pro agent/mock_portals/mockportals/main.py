"""Run the three supplier portals and the private control API in one process, one port each."""

from __future__ import annotations

import asyncio
import os

import uvicorn

from . import db
from .control import create_control_app
from .portal import create_portal_app

PORTS = {
    "alpha": int(os.environ.get("ALPHA_PORT", "8301")),
    "beta": int(os.environ.get("BETA_PORT", "8302")),
    "gamma": int(os.environ.get("GAMMA_PORT", "8303")),
}
CONTROL_PORT = int(os.environ.get("CONTROL_PORT", "8309"))
HOST = os.environ.get("MOCK_HOST", "127.0.0.1")


async def serve() -> None:
    eng = db.engine()
    with eng.connect() as conn:
        if db.get_state(conn)["name"] == "uninitialised":
            db.reset("happy_path")
    servers = [
        uvicorn.Server(uvicorn.Config(create_portal_app(s), host=HOST, port=p, log_level="warning",
                                      timeout_keep_alive=5))
        for s, p in PORTS.items()
    ]
    servers.append(
        uvicorn.Server(uvicorn.Config(create_control_app(), host=os.environ.get("CONTROL_HOST", HOST),
                                      port=CONTROL_PORT, log_level="warning"))
    )
    for s in servers:
        s.install_signal_handlers = lambda: None  # type: ignore[method-assign]
    print(f"Supplier portals: {PORTS}; control API on {CONTROL_PORT}", flush=True)
    await asyncio.gather(*(s.serve() for s in servers))


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
