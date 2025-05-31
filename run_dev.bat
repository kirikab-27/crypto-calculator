@echo off
REM Development startup script for Crypto Calculator (Windows)
REM This script starts both the backend and frontend servers

echo Starting Crypto Calculator Development Servers...
echo =============================================

REM Start backend server in new window
echo Starting backend server on http://localhost:8000...
start "Crypto Calculator Backend" cmd /k "cd backend && python main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server in new window  
echo Starting frontend server on http://localhost:3000...
start "Crypto Calculator Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =============================================
echo Both servers are running in separate windows!
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo Backend API docs: http://localhost:8000/docs
echo.
echo Close both command windows to stop the servers
echo =============================================

pause