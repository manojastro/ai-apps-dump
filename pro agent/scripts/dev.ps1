# Local development on Windows (PowerShell + Docker Desktop).
#   ./scripts/dev.ps1 setup    install deps, start PostgreSQL, migrate, seed, install Chromium
#   ./scripts/dev.ps1 start    start supplier portals, API, worker and UI (separate windows)
#   ./scripts/dev.ps1 check    lint, type-check and tests
#   ./scripts/dev.ps1 reset    DESTRUCTIVE: wipe demo runs/orders and supplier fixtures
param([Parameter(Mandatory = $true)][ValidateSet("setup", "start", "check", "reset")] [string]$Command)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

switch ($Command) {
  "setup" {
    if (-not (Test-Path "$Root/.env")) { Copy-Item "$Root/.env.example" "$Root/.env" }
    docker compose -f "$Root/docker-compose.dev.yml" up -d
    Push-Location "$Root/backend"; uv sync; uv run playwright install chromium; Pop-Location
    Push-Location "$Root/mock_portals"; uv sync; Pop-Location
    Push-Location "$Root/frontend"; npm ci; Pop-Location
    do { Start-Sleep 2 } until ((docker exec procnav-dev-db-1 pg_isready -U postgres) -match "accepting")
    Push-Location "$Root/backend"; uv run python -m procnav.manage migrate; uv run python -m procnav.manage seed; Pop-Location
    Write-Host "Setup complete. Run ./scripts/dev.ps1 start"
  }
  "start" {
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$Root/mock_portals'; uv run python -m mockportals.main"
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$Root/backend'; uv run uvicorn procnav.api.app:app --port 8300"
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$Root/backend'; uv run python -m procnav.workers.main"
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd '$Root/frontend'; npm run dev"
    Write-Host "UI: http://localhost:5273  API docs: http://localhost:8300/api/docs  Portals: 8301-8303"
  }
  "check" {
    Push-Location "$Root/backend"; uv run ruff check .; uv run pytest -q -m "not browser"; Pop-Location
    Push-Location "$Root/mock_portals"; uv run ruff check .; uv run pytest -q; Pop-Location
    Push-Location "$Root/frontend"; npm run typecheck; npm run build; Pop-Location
    Write-Host "Browser scenarios: cd backend; uv run pytest -q -m browser   (portals must be running)"
  }
  "reset" {
    $answer = Read-Host "This deletes demo runs, approvals, orders, evidence and supplier fixture orders. Type RESET"
    if ($answer -ne "RESET") { Write-Host "Aborted"; exit 1 }
    Push-Location "$Root/backend"; uv run python -m procnav.manage reset-demo; Pop-Location
    Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8309/_control/reset" -Headers @{ "X-Control-Token" = "dev-control-token" } -ContentType "application/json" -Body '{"scenario":"happy_path"}'
  }
}
