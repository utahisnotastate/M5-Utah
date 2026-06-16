@echo off
REM Utah-Flux Omniscient Studio — starts UtahClaw daemon and opens the Intent-Resolution Canvas
cd /d "%~dp0.."
echo [UTAH-FLUX] Starting UtahClaw daemon on http://127.0.0.1:8024 ...
start "UtahClaw Daemon" /MIN cmd /c "py -m utah_flux.utahclaw_daemon"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8024"
echo [UTAH-FLUX] Browser opened. Keep the daemon window running while you vibe-code.
