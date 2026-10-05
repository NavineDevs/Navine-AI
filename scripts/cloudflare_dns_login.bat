@echo off
setlocal
where cloudflared >nul 2>&1
if errorlevel 1 (
  echo cloudflared not found on PATH.
  echo Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
  exit /b 1
)

echo.
echo === Cloudflare origin cert login ===
echo A browser window will open. Sign in to the account that owns navinecord.dev
echo and authorize that zone. Wait until this window says login succeeded.
echo.
echo Do NOT copy back cert.pem.bak-20260821 or cert.pem.stale-20260821
echo (those caused Authentication error 10000).
echo.
pause

cloudflared tunnel login
if errorlevel 1 (
  echo Login failed. Use Dashboard CNAMEs instead - see LAUNCH.md Public tunnel.
  exit /b 1
)

if not exist "%USERPROFILE%\.cloudflared\cert.pem" (
  echo Login finished but cert.pem is still missing under %%USERPROFILE%%\.cloudflared\
  echo Use Dashboard CNAMEs in LAUNCH.md, or re-run this script.
  exit /b 1
)

echo.
echo === Routing DNS to tunnel navine-ai ===
cloudflared tunnel route dns navine-ai ai.navinecord.dev
if errorlevel 1 (
  echo Failed: ai.navinecord.dev
  exit /b 1
)
cloudflared tunnel route dns navine-ai pai.navinecord.dev
if errorlevel 1 (
  echo Failed: pai.navinecord.dev
  exit /b 1
)

echo.
echo Done. Verify with:
echo   nslookup ai.navinecord.dev 1.1.1.1
echo   nslookup pai.navinecord.dev 1.1.1.1
echo Then start APIs and cloudflare-tunnel.bat
endlocal
