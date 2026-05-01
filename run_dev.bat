@echo off
echo Starting CurryCast Development Stack...

:: Start Backend (FastAPI)
echo Launching Backend...
start "CurryCast Backend" cmd /k "python -m uvicorn src.api.service:app --reload --port 8000"

:: Start Frontend (React)
echo Launching Frontend...
cd frontend
start "CurryCast Frontend" cmd /k "npm.cmd run dev"

echo.
echo All services are starting!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause
