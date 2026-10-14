$ErrorActionPreference = "Stop"
$force = $false
foreach ($arg in $args) {
    if ($arg -eq "-ForcePublic" -or $arg -eq "--force-public") { $force = $true }
}
if (-not $force) {
    Write-Host "Normal AI public site (ai.navinecord.dev) is disabled."
    Write-Host "PAI public site is separate: scripts\start_pai_cloudflared.ps1"
    Write-Host "To force the normal AI tunnel anyway, re-run with -ForcePublic"
    exit 1
}
$config = Join-Path $env:USERPROFILE ".cloudflared\navine-ai-config.yml"
$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Error "cloudflared not found on PATH"
}
if (-not (Test-Path $config)) {
    Write-Error "Missing tunnel config: $config"
}
Write-Host "Starting Navine AI Cloudflare tunnel"
Write-Host "  ai.navinecord.dev  -> 127.0.0.1:8765"
Write-Host "Config: $config"
& cloudflared tunnel --config $config run navine-ai
