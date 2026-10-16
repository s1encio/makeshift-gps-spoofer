@echo off
echo Installing iPhone Teleport...
python --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo Python is not installed. Get it from https://www.python.org/downloads/
  echo IMPORTANT: tick "Add python.exe to PATH" during install, then run this again.
  pause
  exit /b
)
python --version
python -m pip install --upgrade pip
python -m pip install --upgrade pymobiledevice3 tkintermapview
if errorlevel 1 (
  echo.
  echo ============================================================
  echo  INSTALL FAILED - scroll up to see the error.
  echo  If it mentions "Microsoft Visual C++ 14.0", install the
  echo  Microsoft C++ Build Tools (see README), then run this again.
  echo ============================================================
  pause
  exit /b
)
echo.
echo Done! Now double-click run.bat
pause
