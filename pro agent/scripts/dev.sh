#!/usr/bin/env bash
# Local development on Ubuntu (Docker Engine).
#   scripts/dev.sh setup | start | check | reset
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cmd="${1:-}"
case "$cmd" in
  setup)
    [ -f "$ROOT/.env" ] || cp "$ROOT/.env.example" "$ROOT/.env"
    docker compose -f "$ROOT/docker-compose.dev.yml" up -d
    (cd "$ROOT/backend" && uv sync && uv run playwright install --with-deps chromium)
    (cd "$ROOT/mock_portals" && uv sync)
    (cd "$ROOT/frontend" && npm ci)
    until docker exec procnav-dev-db-1 pg_isready -U postgres >/dev/null 2>&1; do sleep 2; done
    (cd "$ROOT/backend" && uv run python -m procnav.manage migrate && uv run python -m procnav.manage seed)
    echo "Setup complete. Run scripts/dev.sh start"
    ;;
  start)
    mkdir -p "$ROOT/var/log"
    (cd "$ROOT/mock_portals" && uv run python -m mockportals.main >"$ROOT/var/log/portals.log" 2>&1 &)
    (cd "$ROOT/backend" && uv run uvicorn procnav.api.app:app --port 8300 >"$ROOT/var/log/api.log" 2>&1 &)
    (cd "$ROOT/backend" && uv run python -m procnav.workers.main >"$ROOT/var/log/worker.log" 2>&1 &)
    (cd "$ROOT/frontend" && npm run dev >"$ROOT/var/log/frontend.log" 2>&1 &)
    echo "UI: http://localhost:5273  API docs: http://localhost:8300/api/docs  logs: var/log/"
    ;;
  check)
    (cd "$ROOT/backend" && uv run ruff check . && uv run pytest -q -m "not browser")
    (cd "$ROOT/mock_portals" && uv run ruff check . && uv run pytest -q)
    (cd "$ROOT/frontend" && npm run typecheck && npm run build)
    echo "Browser scenarios: (cd backend && uv run pytest -q -m browser)  # portals must be running"
    ;;
  reset)
    read -r -p "This deletes demo runs, approvals, orders, evidence and supplier fixture orders. Type RESET: " answer
    [ "$answer" = "RESET" ] || { echo "Aborted"; exit 1; }
    (cd "$ROOT/backend" && uv run python -m procnav.manage reset-demo)
    curl -fsS -X POST -H "X-Control-Token: ${FIXTURE_CONTROL_TOKEN:-dev-control-token}" -H "Content-Type: application/json" \
      -d '{"scenario":"happy_path"}' http://127.0.0.1:8309/_control/reset
    ;;
  *) echo "usage: scripts/dev.sh setup|start|check|reset"; exit 2 ;;
esac
