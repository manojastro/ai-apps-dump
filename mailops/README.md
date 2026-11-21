# MailOps AI — local prototype

This project is an **incomplete synthetic-data prototype**, not an enterprise-ready application. It provides a local case queue for demonstrating invoice and order review, with a SQLite store and an approval-gated mock executor. The supplied sender address is not authenticated. Do not use real data or connect it to real business systems.

## Run locally (PowerShell)

Requires Python 3.12 and Node.js. From the project directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:PYTHONPATH = 'backend'
$env:MAILOPS_REVIEWER_TOKEN = 'choose-a-local-test-token'
.\.venv\Scripts\python.exe -m uvicorn app.api:app_factory --factory --host 127.0.0.1 --port 8000
```

In another PowerShell window:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173 and enter the token you configured. The Vite development server proxies `/api` to the backend. API documentation is at http://127.0.0.1:8000/docs. The demo order date is fixed at 2027-01-15 and becomes invalid after that date.

Use the invoice or order example in the intake form, create the case, start investigation, review the evidence and approve. The response is stored locally; no email is transmitted. Seed records are synthetic. The order workflow is a simplified mock and does not check real carrier schedules.

## Tests

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run build
```

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for the remaining requirements and security limitations.

## Local container setup

The Compose setup packages the current prototype for local use only. It does not add PostgreSQL, Redis, production authentication, or the missing workflows. It listens on `127.0.0.1:18080` and stores the SQLite database in a Docker volume. Do not expose it to a network or use real data.

Start Docker Desktop, then in PowerShell from the project root set a unique local token and start:

```powershell
$env:MAILOPS_REVIEWER_TOKEN = 'choose-a-strong-unique-local-token'
docker compose up --build
```

Open http://127.0.0.1:18080 and enter that token. `docker compose down` stops the services without deleting the database volume. The local container build and runtime were verified on 2026-11-04. Set MAILOPS_PORT to choose a different local port.

