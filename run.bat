@echo off
REM ResearchMind AI Startup Script for Windows

echo.
echo ========================================
echo   ResearchMind AI - Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create and activate virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
cd backend
echo Installing dependencies...
pip install -q -r requirements.txt
cd ..

REM Create necessary directories
if not exist "data\uploaded_papers" mkdir data\uploaded_papers
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\temp_embeddings" mkdir data\temp_embeddings

echo.
echo ========================================
echo   Services Starting
echo ========================================
echo.

REM Create two separate terminal windows
echo Starting FastAPI Backend on port 8000...
start cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak

echo Starting Streamlit Frontend on port 8501...
start cmd /k "cd frontend && streamlit run streamlit_app.py"

echo.
echo ========================================
echo   Services Started!
echo ========================================
echo.
echo Frontend: http://localhost:8501
echo API:      http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press CTRL+C in each window to stop services
echo.
pause
