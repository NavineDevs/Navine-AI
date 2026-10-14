@echo off
setlocal
echo Normal AI public site (ai.navinecord.dev) is disabled.
echo Use PAI instead: powershell -ExecutionPolicy Bypass -File scripts\start_pai_cloudflared.ps1
echo Or start PAI stack: powershell -ExecutionPolicy Bypass -File scripts\start_public_stack.ps1
if /I "%~1"=="--force-public" goto :force
if /I "%~1"=="-ForcePublic" goto :force
exit /b 1
:force
set "CF_CONFIG=%USERPROFILE%\.cloudflared\navine-ai-config.yml"
where cloudflared >nul 2>&1
if errorlevel 1 (
  echo cloudflared not found.
  exit /b 1
)
if not exist "%CF_CONFIG%" (
  echo Missing tunnel config: %CF_CONFIG%
  exit /b 1
)
echo Starting Navine AI Cloudflare tunnel
cloudflared tunnel --config "%CF_CONFIG%" run navine-ai
endlocal
