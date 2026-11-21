$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8105 --no-server-header
