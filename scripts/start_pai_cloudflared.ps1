$ErrorActionPreference = "Stop"
$config = Join-Path $env:USERPROFILE ".cloudflared\navine-pai-config.yml"
$tunnelId = "d7eff602-b8a9-40c8-9341-89f1668d996c"
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Error "cloudflared not found on PATH"
}
if (-not (Test-Path $config)) {
    Write-Error "Missing tunnel config: $config"
}
Write-Host "Starting PAI Cloudflare tunnel ($tunnelId)"
Write-Host "  pai.navinecord.dev -> 127.0.0.1:8766"
Write-Host "  (normal ai.navinecord.dev stays off)"
Write-Host "Config: $config"
& cloudflared tunnel --config $config run $tunnelId
