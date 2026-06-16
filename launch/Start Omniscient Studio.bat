@echo off
REM Utah-Flux Omniscient OS — auto-discovery deck (no LLM required)
cd /d "%~dp0.."
echo [UTAH-FLUX] Starting Omniscient daemon on http://127.0.0.1:8000 ...
start "Omniscient Daemon" /MIN cmd /c "py -m utah_flux.omniscient_daemon"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000"
echo [UTAH-FLUX] Discovery deck ready. Plug in CoreS3 via USB-C.
