@echo off
setlocal enabledelayedexpansion

echo ====================================================
echo Starting OTSi ESS Portal Backend...
echo ====================================================

:: Navigate to ESS_Backend directory using relative script directory
cd /d "%~dp0ESS_Backend"

:: Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [!] Virtual environment not found.
    echo Running automated setup first...
    call "%~dp0setup_laptop.bat"
    if errorlevel 1 exit /b 1
)

:: Activate virtual environment and start server
call venv\Scripts\activate.bat
echo [✓] Virtual environment activated.
echo [✓] Starting Flask Server on http://127.0.0.1:5000 ...
python app.py
pause
