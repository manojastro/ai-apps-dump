# Selected versions (verified at implementation time, October 2026)

| Component | Version | Notes |
|---|---|---|
| Python | 3.12 (uv-managed, `>=3.12,<3.14`) | |
| uv | 0.11.20 | lockfiles: `backend/uv.lock`, `mock_portals/uv.lock` |
| FastAPI | 0.142.2 | |
| Pydantic | 2.13.5 | |
| SQLAlchemy | 2.1.3 | |
| Alembic | 1.20.0 | |
| psycopg | 3.3.6 (binary) | |
| LangGraph | 1.2.14 | `langgraph-checkpoint-postgres` 3.1.2 (PostgresSaver, interrupts) |
| Playwright (Python) | 1.63.0 | Container image **`mcr.microsoft.com/playwright/python:v1.63.0-noble`** (matching Chromium + Linux deps); seccomp profile from Playwright v1.63.0 `utils/docker/seccomp_profile.json` |
| anthropic (Python SDK) | 1.11.0 | default model `claude-opus-5-5`; structured outputs via `client.beta.messages.parse`; `server-side-fallback-2026-07-01` |
| argon2-cffi, cryptography, PyJWT | latest at lock time | see `uv.lock` |
| PostgreSQL | 17 (alpine image) | |
| Node.js | 22 | npm 10.9.2 pinned via `packageManager`; `frontend/package-lock.json` |
| React | 19.2 | Vite 8.3, TypeScript 6.0, Tailwind CSS 4.3, Radix UI primitives, TanStack Query 5, React Router 7 |
| Caddy | 2.10 | production TLS reverse proxy |
| Ruff / pytest | 0.16.10 / 9.1.1 | |

Linux runtime requirements for Chromium are satisfied by the Playwright image. On a bare Ubuntu host,
`uv run playwright install --with-deps chromium` installs them.
