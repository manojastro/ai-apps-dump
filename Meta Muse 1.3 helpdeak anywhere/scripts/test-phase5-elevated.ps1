#Requires -RunAsAdministrator
<#
  Phase 5 elevated UAC-cycle test. Run ONCE from an elevated PowerShell:
    powershell -ExecutionPolicy Bypass -File scripts/test-phase5-elevated.ps1
  What it does (all automatic after launch):
  1. Starts the dev server locally.
  2. Runs scripts/verify-phase5-uac.mjs, performing privileged INSTALL /
     TRIGGER_UAC / UNINSTALL steps on demand over a DONE protocol.
  3. Raises ONE real UAC consent prompt (unelevated trigger) and dismisses it
     remotely with Escape through the helper. If dismissal fails, the prompt
     stays on screen for one manual click on No (benign) and the run reports
     PENDING instead of PASS.
  Your screen will flash to the secure desktop for ~30s. Nothing is installed
  afterwards: the service is removed and %ProgramData%\HelpdeskAnywhere is gone.
  Exit codes: 0 pass, 1 fail, 2 pending-human.
#>
$ErrorActionPreference = "Stop"
param([int]$Port = 18103)

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Write-Host "Run this script from an ELEVATED PowerShell (Run as Administrator)."
  exit 2
}

$repoRoot = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $repoRoot "server\public\download\HelpdeskAnywhere.exe"
if (-not (Test-Path -LiteralPath $exe)) {
  Write-Host "Missing $exe — run scripts/build-windows.ps1 first."
  exit 1
}

$serverJob = Start-Job -ScriptBlock {
  param($root, $port)
  Set-Location (Join-Path $root "server")
  $env:PORT = "$port"
  $env:AUDIT_PATH = "data/uac-elevated.jsonl"
  $env:PUBLIC_HOST = "127.0.0.1:$port"
  node dist/index.js
} -ArgumentList $repoRoot, $Port

function Done-Install([string]$pipe) {
  Write-Host "[ps1] installing service..."
  & $exe --install-service --pipe $pipe
  if ($LASTEXITCODE -ne 0) { return "DONE install FAIL installer-exit=$LASTEXITCODE" }
  Start-Sleep -Seconds 2
  $q = sc.exe query HelpdeskAnywhereSvc 2>&1 | Out-String
  if ($q -notmatch "RUNNING") { return "DONE install FAIL not-running" }
  return "DONE install ok"
}

function Done-TriggerUac {
  Write-Host "[ps1] raising real UAC prompt from unelevated process..."
  # runas /trustlevel drops privileges; the inner Start-Process -Verb RunAs
  # then raises a genuine consent prompt on the Winlogon desktop.
  cmd /c 'runas /trustlevel:0x20000 "powershell -NoProfile -NonInteractive -Command Start-Sleep -Seconds 1; Start-Process cmd.exe -Verb RunAs"' 2>&1 | Out-Null
  Start-Sleep -Seconds 4
  return "DONE trigger ok"
}

function Done-Uninstall {
  Write-Host "[ps1] uninstalling service..."
  & $exe --uninstall-service --pipe none 2>&1 | Out-Null
  Start-Sleep -Seconds 2
  $q = sc.exe query HelpdeskAnywhereSvc 2>&1 | Out-String
  $gone = ($q -match "FAILED 1060") -or ($q -match "does not exist")
  $dir = Join-Path ([Environment]::GetFolderPath("CommonApplicationData")) "HelpdeskAnywhere"
  $dirGone = -not (Test-Path -LiteralPath $dir)
  if ($gone -and $dirGone) { return "DONE uninstall ok" }
  return "DONE uninstall PENDING sc-gone=$gone dir-gone=$dirGone"
}

$psi = New-Object System.Diagnostics.ProcessStartInfo("node", "scripts/verify-phase5-uac.mjs --http http://127.0.0.1:$Port --url ws://127.0.0.1:$Port/ws")
$psi.WorkingDirectory = $repoRoot
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$proc = [System.Diagnostics.Process]::Start($psi)
$proc.ErrorDataReceived += { param($s, $e) if ($e.Data) { Write-Host "[uac:err] $($e.Data)" } }
try {
  while (($line = $proc.StandardOutput.ReadLine()) -ne $null) {
    if ($line.StartsWith("ACTION:")) {
      $reply = "DONE unknown"
      if ($line -match "^ACTION:INSTALL pipe=(\S+)") { $reply = Done-Install $Matches[1] }
      elseif ($line -eq "ACTION:TRIGGER_UAC") { $reply = Done-TriggerUac }
      elseif ($line -eq "ACTION:UNINSTALL") { $reply = Done-Uninstall }
      Write-Host "[ps1] <- $line"
      Write-Host "[ps1] -> $reply"
      $proc.StandardInput.WriteLine($reply)
    } else {
      Write-Host "[uac] $line"
    }
  }
  $proc.WaitForExit()
  $code = $proc.ExitCode
} finally {
  Stop-Job $serverJob -ErrorAction SilentlyContinue
  Remove-Job $serverJob -Force -ErrorAction SilentlyContinue
}
Write-Host "elevated UAC test exit=$code"
exit $code
