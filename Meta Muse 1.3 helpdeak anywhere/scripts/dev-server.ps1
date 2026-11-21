$ErrorActionPreference = "Stop"

# Local dev server on Windows (Node run directly, no Docker required)
$repoRoot = Split-Path $PSScriptRoot -Parent
$serverDir = Join-Path $repoRoot "server"

if (-not (Test-Path (Join-Path $serverDir "node_modules"))) {
  Write-Host "Installing server dependencies..."
  npm --prefix $serverDir install
}

npm --prefix $serverDir run dev
