@echo off
echo Starting TRACE Backend Server...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then activate it and install dependencies: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run server
echo Server running at http://localhost:8000
echo API docs at http://localhost:8000/docs
echo.
uvicorn main:app --reload --host 0.0.0.0 --port 8000
