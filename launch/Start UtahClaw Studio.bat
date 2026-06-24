@echo off
REM Utah-Flux Intent-Resolution Canvas — UtahClaw daemon (port 8024)
cd /d "%~dp0.."

set "PY=py"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

echo [UTAH-FLUX] Checking UtahClaw dependencies...
"%PY%" -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
  echo [UTAH-FLUX] Installing host[claw] one-time — FastAPI, Uvicorn, Ollama...
  "%PY%" -m pip install -e "./host[claw]"
  if errorlevel 1 (
    echo.
    echo [ERROR] Could not install UtahClaw. Install Python 3.10+ and run:
    echo   pip install -e "host[claw]"
    pause
    exit /b 1
  )
)

echo [UTAH-FLUX] Starting UtahClaw daemon on http://127.0.0.1:8024 ...
start "UtahClaw Daemon" cmd /k ""%PY%" -m utah_flux.utahclaw_daemon"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8024"
echo [UTAH-FLUX] Browser opened. Keep the "UtahClaw Daemon" window running while you vibe-code.
echo If the page fails to load, check that window for errors.
