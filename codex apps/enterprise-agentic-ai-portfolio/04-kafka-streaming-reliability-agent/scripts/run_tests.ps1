$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $projectRoot 'backend'
python -m unittest discover -s (Join-Path $projectRoot 'tests') -v
