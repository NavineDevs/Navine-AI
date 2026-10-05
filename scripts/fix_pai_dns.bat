@echo off

setlocal

set TUNNEL_ID=d7eff602-b8a9-40c8-9341-89f1668d996c

set TUNNEL_TARGET=%TUNNEL_ID%.cfargotunnel.com

echo.

echo pai.navinecord.dev uses tunnel "pai" (%TUNNEL_ID%)

echo.

where cloudflared >nul 2>&1

if errorlevel 1 (

  echo Install cloudflared first.

  exit /b 1

)



echo Step 1: Try DNS route via cloudflared (does not modify cert.pem)

cloudflared tunnel route dns --overwrite-dns pai pai.navinecord.dev

if errorlevel 1 (

  echo.

  echo CLI failed. Add manually in Cloudflare Dashboard -^> navinecord.dev -^> DNS:

  echo   Type CNAME  Name pai  Target %TUNNEL_TARGET%  Proxied ON

  echo.

  nslookup pai.navinecord.dev 1.1.1.1

  exit /b 1

)



echo.

echo Verify:

nslookup pai.navinecord.dev 1.1.1.1

echo.

echo Then run: scripts\start_public_stack.ps1

endlocal

