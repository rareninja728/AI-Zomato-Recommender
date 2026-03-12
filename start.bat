@echo off
title Zomato AI - Starting...
color 0A

echo.
echo  =====================================================
echo   Zomato AI Restaurant Recommendation Service
echo  =====================================================
echo.
echo  [1/3] Starting backend API server on port 8000...
echo.

:: Start the FastAPI backend in a new terminal window
start "Zomato AI Backend" cmd /k "cd /d "%~dp0PHASE 5" && python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait a few seconds for the server to boot up before opening the browser
echo  [2/3] Waiting for server to start (5 seconds)...
timeout /t 5 /nobreak >nul

:: Open the frontend in the default browser
echo  [3/3] Opening the Zomato AI frontend in your browser...
start "" "http://localhost:8000"

echo.
echo  [OK] Zomato AI is running!
echo  [OK] Backend: http://localhost:8000
echo  [OK] Frontend: PHASE 4\frontend\index.html
echo.
echo  Keep the "Zomato AI Backend" terminal window open.
echo  Close this window when done.
echo.
pause
