@echo off
echo Installing UtahClaw Studio (one time)...
cd /d "%~dp0"
set "PY=py"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install -e "./host[claw]"
if errorlevel 1 (
  echo.
  echo Install failed. Please install Python 3.10+ from https://www.python.org/
  pause
  exit /b 1
)
echo.
echo Done! Now double-click "Start UtahClaw Studio.bat"
pause
