@echo off
echo Starting Kulture32 Setup and Development Stack...

:: Set Environment Variable for Data Generation
set RESTAURANT_PROFILE=kulture32

echo 1. Generating synthetic data for Kulture32...
python scripts/generate_synthetic_data.py
if %ERRORLEVEL% NEQ 0 (
    echo Error during data generation. Exiting...
    pause
    exit /b %ERRORLEVEL%
)

echo 2. Training model for Kulture32...
python scripts/train_model.py --profile kulture32
if %ERRORLEVEL% NEQ 0 (
    echo Error during model training. Exiting...
    pause
    exit /b %ERRORLEVEL%
)

echo 3. Launching Backend (FastAPI)...
start "CurryCast Backend" cmd /k "python -m uvicorn src.api.service:app --reload --port 8000"

echo 4. Launching Frontend (React)...
cd frontend
start "CurryCast Frontend" cmd /k "npm.cmd run dev"

echo.
echo Kulture32 services are starting!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause
