$ErrorActionPreference = "Stop"
$tunnelName = "pai"
$tunnelId = "d7eff602-b8a9-40c8-9341-89f1668d996c"
$tunnelTarget = "$tunnelId.cfargotunnel.com"
$hostname = "pai.navinecord.dev"
$credFile = Join-Path $env:USERPROFILE ".cloudflared\$tunnelId.json"

function Test-PaiDns {
    try {
        Resolve-DnsName $hostname -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host ""
Write-Host "pai.navinecord.dev setup"
Write-Host "========================"
Write-Host "Tunnel: $tunnelName ($tunnelId)"
Write-Host ""

if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    exit 1
}

if (-not (Test-Path $credFile)) {
    Write-Host "Missing credentials: $credFile"
    exit 1
}

if (Test-PaiDns) {
    Write-Host "DNS OK: $hostname resolves."
    try {
        $code = (Invoke-WebRequest -Uri "https://$hostname/api/health" -UseBasicParsing -TimeoutSec 20).StatusCode
        Write-Host "Public health: HTTP $code"
    } catch {
        Write-Host "DNS resolves but HTTPS check failed: $($_.Exception.Message)"
        Write-Host "Ensure PAI tunnel is running (scripts\start_public_stack.ps1)."
    }
    exit 0
}

Write-Host "Missing DNS for $hostname (NXDOMAIN)."
Write-Host ""
Write-Host "Trying cloudflared tunnel route dns (uses existing cert.pem if valid)..."
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& cloudflared tunnel route dns --overwrite-dns $tunnelName $hostname 2>&1 | Write-Host
$ErrorActionPreference = $prev
Start-Sleep -Seconds 3

if (Test-PaiDns) {
    Write-Host "OK: $hostname DNS created."
    Write-Host "Verify: curl https://$hostname/api/health"
    exit 0
}

Write-Host ""
Write-Host "CLI route failed (cert auth or zone permissions). Add this in Cloudflare Dashboard -> navinecord.dev -> DNS:"
Write-Host "  Type: CNAME"
Write-Host "  Name: pai"
Write-Host "  Target: $tunnelTarget"
Write-Host "  Proxy: ON (orange cloud)"
Write-Host ""
Write-Host "Then run: powershell -ExecutionPolicy Bypass -File scripts\start_public_stack.ps1"
Write-Host ""
exit 1
