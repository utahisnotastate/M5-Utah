@echo off
echo Installing Utah Flux Studio (one time)...
cd /d "%~dp0host"
python -m pip install -e .
if errorlevel 1 (
  echo.
  echo Install failed. Please install Python 3.10+ from https://www.python.org/
  pause
  exit /b 1
)
echo.
echo Done! Now double-click "Start Utah Flux Studio.bat"
pause
