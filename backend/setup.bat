@echo off
echo ================================================================
echo TRACE Backend - Quick Setup Script
echo ================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo     Virtual environment created successfully

echo.
echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo.
echo [4/6] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo     Dependencies installed successfully

echo.
echo [5/6] Initializing database...
python -c "from app.db.database import init_db; init_db(); print('Database initialized')"
if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    pause
    exit /b 1
)

echo.
echo [6/6] Seeding demo data...
python scripts\seed_data.py
if errorlevel 1 (
    echo [WARNING] Failed to seed data (you can run scripts\seed_data.py later)
)

echo.
echo ================================================================
echo Setup Complete!
echo ================================================================
echo.
echo To start the server:
echo   1. Activate the virtual environment: venv\Scripts\activate.bat
echo   2. Run the server: uvicorn main:app --reload
echo   Or simply run: run_server.bat
echo.
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Demo Users (password: password123):
echo   - client_user (CLIENT_EMPLOYEE)
echo   - ai_auditor (INDEPENDENT_AI_AUDITOR)
echo   - human_auditor (HUMAN_AUDITOR)
echo   - admin_user (PLATFORM_ADMIN)
echo.
echo See INSTALL.md for detailed instructions
echo See README.md for API documentation
echo.
pause
