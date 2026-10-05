$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$pyRoot = Join-Path (Split-Path $root -Parent) "Navine AI - Python"
$pyAlt = Join-Path $pyRoot "venv\Scripts\python.exe"
$cfPaiConfig = Join-Path $env:USERPROFILE ".cloudflared\navine-pai-config.yml"
$paiTunnelId = "d7eff602-b8a9-40c8-9341-89f1668d996c"
$logDir = Join-Path $root "logs"
$forceAi = $false
foreach ($arg in $args) {
    if ($arg -eq "-ForceAiPublic" -or $arg -eq "--force-ai-public") { $forceAi = $true }
}

function Stop-PortListener([int]$Port) {
    $line = netstat -ano | Select-String "127.0.0.1:$Port\s+.*LISTENING"
    if (-not $line) { return }
    $procId = ($line.ToString().Trim() -split '\s+')[-1]
    if ($procId -match '^\d+$') {
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
    }
}

function Start-NavineServer([string]$ProjectRoot, [int]$Port, [string]$Tag) {
    $py = Join-Path $ProjectRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { throw "Missing python: $py" }
    Stop-PortListener $Port
    Start-Sleep -Seconds 1
    $out = Join-Path $logDir "server_${Port}.out.log"
    $err = Join-Path $logDir "server_${Port}.err.log"
    Start-Process -FilePath $py -ArgumentList "-u", "-m", "navine.server", "--port", "$Port" `
        -WorkingDirectory $ProjectRoot -WindowStyle Hidden `
        -RedirectStandardOutput $out -RedirectStandardError $err
    Write-Host "Started $Tag on http://127.0.0.1:$Port"
}

if (-not (Test-Path $pyAlt)) { throw "Missing python site venv: $pyAlt" }
if (-not (Test-Path $cfPaiConfig)) { throw "Missing PAI cloudflared config: $cfPaiConfig" }

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Write-Host "Public mode: PAI on (pai.navinecord.dev). Normal AI public stays off."
Start-NavineServer $pyRoot 8766 "Navine AI - Python (pai.navinecord.dev)"

if ($forceAi) {
    $pyMain = Join-Path $root "venv\Scripts\python.exe"
    $cfConfig = Join-Path $env:USERPROFILE ".cloudflared\navine-ai-config.yml"
    if (-not (Test-Path $pyMain)) { throw "Missing main venv: $pyMain" }
    if (-not (Test-Path $cfConfig)) { throw "Missing cloudflared config: $cfConfig" }
    Start-NavineServer $root 8765 "Navine AI"
}

Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $cmd = $_.CommandLine
        if ($forceAi -or ($cmd -match 'navine-pai|d7eff602')) {
            if ($cmd -match 'navine-ai-config' -and -not $forceAi) { return }
        }
        if ($cmd -match 'navine-pai|d7eff602' -or ($forceAi -and $cmd -match 'navine-ai')) {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        } elseif ($cmd -match 'navine-ai-config|run navine-ai') {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
Start-Sleep -Seconds 1

Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue |
    ForEach-Object {
        if ($_.CommandLine -match 'navine-ai-config|run navine-ai') {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped normal AI tunnel (ai.navinecord.dev stays off)"
        }
    }

$cfPaiOut = Join-Path $logDir "cloudflared_pai.out.log"
$cfPaiErr = Join-Path $logDir "cloudflared_pai.err.log"
Start-Process -FilePath "cloudflared" -ArgumentList "tunnel", "--config", $cfPaiConfig, "run", $paiTunnelId `
    -WindowStyle Hidden -RedirectStandardOutput $cfPaiOut -RedirectStandardError $cfPaiErr
Write-Host "Started Cloudflare tunnel pai ($paiTunnelId -> pai.navinecord.dev :8766)"

if ($forceAi) {
    $cfConfig = Join-Path $env:USERPROFILE ".cloudflared\navine-ai-config.yml"
    $cfOut = Join-Path $logDir "cloudflared.out.log"
    $cfErr = Join-Path $logDir "cloudflared.err.log"
    Start-Process -FilePath "cloudflared" -ArgumentList "tunnel", "--config", $cfConfig, "run", "navine-ai" `
        -WindowStyle Hidden -RedirectStandardOutput $cfOut -RedirectStandardError $cfErr
    Write-Host "Started Cloudflare tunnel navine-ai (ai.navinecord.dev -> 8765)"
}

Start-Sleep -Seconds 6
try {
    $h2 = Invoke-RestMethod -Uri "http://127.0.0.1:8766/api/health" -TimeoutSec 8
    Write-Host "Health 8766: $($h2.status)"
} catch {
    Write-Warning "Local PAI health check pending: $_"
}

Write-Host "Public: https://pai.navinecord.dev"
Write-Host "Normal AI public: off (local only http://127.0.0.1:8765 if server is running)"
