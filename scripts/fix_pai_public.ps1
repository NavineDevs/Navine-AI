$ErrorActionPreference = "Stop"
$tunnelId = "d7eff602-b8a9-40c8-9341-89f1668d996c"
$tunnelName = "pai"
$tunnelTarget = "$tunnelId.cfargotunnel.com"
$hostname = "pai.navinecord.dev"
$credFile = Join-Path $env:USERPROFILE ".cloudflared\$tunnelId.json"
$cfPaiConfig = Join-Path $env:USERPROFILE ".cloudflared\navine-pai-config.yml"

Write-Host ""
Write-Host "PAI public URL fix"
Write-Host "=================="
Write-Host "Tunnel: $tunnelName ($tunnelId)"
Write-Host ""

if (-not (Test-Path $credFile)) {
    Write-Host "Missing: $credFile"
    exit 1
}

if (-not (Test-Path $cfPaiConfig)) {
    Write-Host "Missing: $cfPaiConfig"
    exit 1
}

try {
    Resolve-DnsName $hostname -ErrorAction Stop | Out-Null
    Write-Host "DNS OK: $hostname resolves."
} catch {
    Write-Host "DNS MISSING: $hostname does not resolve."
    Write-Host ""
    Write-Host "Cloudflare Dashboard -> navinecord.dev -> DNS:"
    Write-Host "  CNAME  pai  ->  $tunnelTarget  (Proxied ON)"
    Write-Host ""
    Write-Host "Or run: powershell -ExecutionPolicy Bypass -File scripts\setup_pai_dns.ps1"
}

$pyBrand = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "Navine AI - Python\configs\brand.yaml"
if (Test-Path $pyBrand) {
    Write-Host ""
    Write-Host "PAI app: Navine AI - Python on port 8766"
    Write-Host "Config: $pyBrand"
}

Write-Host ""
Write-Host "Start stack: powershell -ExecutionPolicy Bypass -File scripts\start_public_stack.ps1"
Write-Host ""
