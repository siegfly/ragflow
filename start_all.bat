@echo off
echo Starting RAGFlow services...

:: 1. Start Backend in a new window
start "RAGFlow Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\python launch_backend_dev.py"

:: 2. Wait a few seconds for backend to init
timeout /t 5

:: 3. Start Frontend in a new window
start "RAGFlow Frontend" cmd /k "cd /d %~dp0\web && npm run dev"

echo All services started!
