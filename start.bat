@echo off
echo Starting Crystal System...

cd /d %~dp0

echo.
echo [1/2] Starting Backend API...
start "Crystal API" cmd /k "python -m uvicorn app.main:app --reload --port 8000"

echo.
echo [2/2] Starting Frontend Dev Server...
cd app\web
start "Crystal Web" cmd /k "npm run dev"

echo.
echo Crystal System Started!
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5173
echo - API Docs: http://localhost:8000/docs
echo.
pause
