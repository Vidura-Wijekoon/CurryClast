@echo off
echo CurryCast Public Sharing Script
echo -------------------------------
echo This script will create temporary public URLs for your local services.
echo Requirements: Node.js (npx)
echo.

:: Check for npx
where npx >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js/npx not found. Please install Node.js to use this script.
    pause
    exit /b 1
)

echo Starting Backend Tunnel (Port 8000)...
start "Backend Tunnel" cmd /k "npx localtunnel --port 8000"

echo Starting Frontend Tunnel (Port 5173)...
start "Frontend Tunnel" cmd /k "npx localtunnel --port 5173"

echo.
echo Tunnels are starting! 
echo Check the new windows for your public URLs (e.g., https://curvy-cats-run.loca.lt)
echo.
echo IMPORTANT: 
echo 1. You may need to click 'Continue' on the localtunnel landing page.
echo 2. Update your VITE_API_BASE in the frontend if you want them to talk over the public URL.
echo.
pause
