@echo off
setlocal enabledelayedexpansion

color 0A
echo.
echo =======================================================================
echo     OTSi ESS Portal - Automated Personal Laptop Setup ^& Build Script
echo =======================================================================
echo.

:: 1. Check Python
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo [X] ERROR: Python 3.8+ is not installed or not found in system PATH.
    echo.
    echo How to fix:
    echo 1. Download Python from https://www.python.org/downloads/
    echo 2. During installation, CHECK the box "Add Python to PATH"
    echo 3. Restart your terminal/computer and run this script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYTHON_VER=%%v
echo [OK] Found: %PYTHON_VER%

:: 2. Setup Virtual Environment
echo.
echo [2/4] Setting up Python virtual environment (venv)...
set BACKEND_DIR=%~dp0ESS_Backend

if not exist "%BACKEND_DIR%\venv" (
    echo [*] Creating virtual environment at: %BACKEND_DIR%\venv
    python -m venv "%BACKEND_DIR%\venv"
    if errorlevel 1 (
        color 0C
        echo [X] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo [OK] Existing virtual environment found.
)

:: 3. Install Dependencies
echo.
echo [3/4] Installing / Updating Python dependencies...
call "%BACKEND_DIR%\venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install --no-cache-dir -r "%BACKEND_DIR%\requirements.txt"

if errorlevel 1 (
    color 0C
    echo [X] Failed to install required Python packages.
    echo Please ensure you are connected to the internet.
    pause
    exit /b 1
)
echo [OK] All Python dependencies installed successfully.

:: 4. Check Environment Configuration (.env)
echo.
echo [4/4] Checking backend configuration (.env)...

if not exist "%BACKEND_DIR%\.env" (
    echo [*] Creating .env file from template...
    if exist "%BACKEND_DIR%\.env.example" (
        copy "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    ) else (
        (
            echo FLASK_ENV=development
            echo FLASK_DEBUG=True
            echo FLASK_APP=app.py
            echo JWT_SECRET_KEY=otsi-secret-key-%RANDOM%-%RANDOM%-%RANDOM%
            echo SUPABASE_URL=https://your-project.supabase.co
            echo SUPABASE_KEY=your-supabase-api-key
            echo CORS_ORIGINS=http://localhost:5000,http://localhost:3000,http://127.0.0.1:5000
            echo SERVER_PORT=5000
            echo SERVER_HOST=0.0.0.0
        ) > "%BACKEND_DIR%\.env"
    )
    echo [OK] .env file created at: %BACKEND_DIR%\.env
) else (
    echo [OK] Existing .env file found.
)

echo.
echo =======================================================================
echo                     *** BUILD ^& SETUP COMPLETE! ***
echo =======================================================================
echo.
echo  NEXT STEPS TO RUN ON YOUR PERSONAL LAPTOP:
echo.
echo  1. SUPABASE DATABASE SETUP (If not created yet):
echo     - Go to https://supabase.com (Sign up for free)
echo     - Create a new project and go to SQL Editor
echo     - Copy and run the SQL file: ESS_Backend\database_schema.sql
echo     - Copy your Supabase URL ^& API Key into: ESS_Backend\.env
echo.
echo  2. START THE SERVER ^& PORTAL:
echo     - Run `start_server.bat` in this folder
echo     - Or run: cd ESS_Backend ^&^& python app.py
echo.
echo  3. ACCESS THE APPLICATION:
echo     - Web App / Login Page: Open `otsi-attendance-portal.html` in your browser
echo     - Backend API: http://127.0.0.1:5000
echo.
echo =======================================================================
echo.

set /p START_NOW="Would you like to start the portal server right now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo.
    echo Starting OTSi ESS Portal Backend...
    cd /d "%BACKEND_DIR%"
    python app.py
) else (
    echo.
    echo You can start the server anytime by running `start_server.bat`.
    pause
)
