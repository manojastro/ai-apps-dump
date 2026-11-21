$ErrorActionPreference = "Stop"

# Publish Applet (+ Phase 5 service payloads) as self-contained win-x64
# single file(s) into server/public/download/
$repoRoot = Split-Path $PSScriptRoot -Parent
$publishDir = Join-Path ([System.IO.Path]::GetTempPath()) "hda-publish"
Remove-Item $publishDir -Recurse -Force -ErrorAction SilentlyContinue

$svcDir = Join-Path ([System.IO.Path]::GetTempPath()) "hda-svc"
Remove-Item $svcDir -Recurse -Force -ErrorAction SilentlyContinue

# Service + helper publish first so the applet can embed them (single .exe download).
dotnet publish (Join-Path $repoRoot "windows\SecureDesktopService\SecureDesktopService.csproj") `
  -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true `
  -o (Join-Path $svcDir "svc")
if ($LASTEXITCODE -ne 0) { throw "service publish failed" }

dotnet publish (Join-Path $repoRoot "windows\DesktopHelper\DesktopHelper.csproj") `
  -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true `
  -o (Join-Path $svcDir "helper")
if ($LASTEXITCODE -ne 0) { throw "helper publish failed" }

$resDir = Join-Path $repoRoot "windows\Applet\Resources"
New-Item -ItemType Directory -Path $resDir -Force | Out-Null
Copy-Item (Join-Path $svcDir "svc\SecureDesktopService.exe") (Join-Path $resDir "SecureDesktopService.exe") -Force
Copy-Item (Join-Path $svcDir "helper\DesktopHelper.exe") (Join-Path $resDir "DesktopHelper.exe") -Force

dotnet publish (Join-Path $repoRoot "windows\Applet\Applet.csproj") `
  -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true `
  -o $publishDir
if ($LASTEXITCODE -ne 0) { throw "applet publish failed" }

$destDir = Join-Path $repoRoot "server\public\download"
New-Item -ItemType Directory -Path $destDir -Force | Out-Null

Copy-Item (Join-Path $publishDir "Applet.exe") `
  (Join-Path $destDir "HelpdeskAnywhere.exe") -Force

Write-Host "-> server/public/download/HelpdeskAnywhere.exe"
