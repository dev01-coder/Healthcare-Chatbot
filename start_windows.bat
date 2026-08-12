@echo off
echo ============================================
echo   Healthcare RAG Chatbot - Windows Startup
echo ============================================

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

:: Check if .env exists
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo !! IMPORTANT: Edit .env and add your GROQ_API_KEY !!
    echo    Get free key at: https://console.groq.com
    echo.
    pause
)

:: Install Python deps if needed
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo Installing Python dependencies...
pip install -r requirements.txt --quiet

:: Download and process data
if not exist data\processed\all_documents.json (
    echo.
    echo Downloading datasets...
    python scripts/download_data.py
    echo.
    echo Processing data...
    python scripts/process_data.py
)

:: Build index if needed
if not exist data\chroma_db (
    echo.
    echo Building vector index (first time, may take 2-3 minutes)...
    python scripts/build_index.py
)

:: Install frontend deps
if not exist frontend\node_modules (
    echo.
    echo Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

:: Start backend in new window
echo.
echo Starting backend server...
start "Healthcare Bot - Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn backend.api.main:app --reload --port 8000"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in new window
echo Starting frontend...
start "Healthcare Bot - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo  Both servers starting...
echo  Frontend: http://localhost:5173
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:5173

pause
