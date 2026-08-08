@echo off
echo ===================================================
echo Starting Sentinel Fraud Platform...
echo ===================================================

echo [1/3] Starting Backend Server (FastAPI)...
start "Sentinel Backend" cmd /k "cd Backend && ..\venv\Scripts\python.exe -m uvicorn main:app --port 8000"

echo [2/2] Starting Frontend Server...
start "Frontend UI" cmd /k "cd front_end && ..\venv\Scripts\python.exe -m http.server 3000"

echo.
echo All services have been launched in separate windows!
echo.
echo Please wait a few seconds for the servers to boot up, then open your browser to:
echo http://localhost:3000
echo.
pause
