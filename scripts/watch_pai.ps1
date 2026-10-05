$ErrorActionPreference = "Continue"
$paiDir = "C:\Users\hitbo\Downloads\Navine AI - Python"
$aiDir = "C:\Users\hitbo\Downloads\Navine AI"
$paiPy = Join-Path $paiDir "venv\Scripts\python.exe"
$config = Join-Path $env:USERPROFILE ".cloudflared\navine-pai-config.yml"
$tunnelId = "d7eff602-b8a9-40c8-9341-89f1668d996c"
$logDir = Join-Path $aiDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $paiDir "logs") | Out-Null
$watchLog = Join-Path $logDir "pai_watchdog.log"

function Write-Watch([string]$msg) {
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  Add-Content -Path $watchLog -Value $line
  Write-Host $line
}

function Test-LocalPai {
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:8766/api/health" -UseBasicParsing -TimeoutSec 4
    return ($r.StatusCode -eq 200)
  } catch {
    return $false
  }
}

function Ensure-PaiServer {
  if (Test-LocalPai) { return }
  Write-Watch "PAI server down; restarting on 8766"
  Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match 'navine\.server' -and $_.CommandLine -match '8766'
  } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
  $out = Join-Path $paiDir "logs\server_8766.out.log"
  $err = Join-Path $paiDir "logs\server_8766.err.log"
  Start-Process -FilePath $paiPy -ArgumentList @("-u", "-m", "navine.server", "--port", "8766") -WorkingDirectory $paiDir -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 2
    if (Test-LocalPai) {
      Write-Watch "PAI server healthy"
      return
    }
  }
  Write-Watch "PAI server failed to become healthy"
}

function Ensure-Cloudflared {
  $alive = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match 'cloudflared' -and $_.CommandLine -match 'd7eff602'
  }
  if ($alive) { return }
  $cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
  if (-not $cf) {
    $candidates = @(
      "$env:LOCALAPPDATA\cloudflared\cloudflared.exe",
      "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe",
      "$env:ProgramFiles\cloudflared\cloudflared.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $cf = $c; break } }
  }
  if (-not $cf -or -not (Test-Path $config)) {
    Write-Watch "cloudflared or config missing"
    return
  }
  Write-Watch "Starting PAI cloudflared tunnel"
  $out = Join-Path $logDir "cloudflared_pai.out.log"
  $err = Join-Path $logDir "cloudflared_pai.err.log"
  Start-Process -FilePath $cf -ArgumentList @("tunnel", "--config", $config, "run", $tunnelId) -WorkingDirectory $aiDir -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
}

Write-Watch "PAI watchdog started"
while ($true) {
  try {
    Ensure-PaiServer
    Ensure-Cloudflared
  } catch {
    Write-Watch ("watchdog error: " + $_.Exception.Message)
  }
  Start-Sleep -Seconds 20
}
