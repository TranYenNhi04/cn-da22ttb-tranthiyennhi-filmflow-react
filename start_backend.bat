@echo off
REM Start the Movie Recommendation Backend

echo ====================================
echo   Movie Recommendation Backend
echo ====================================
echo.

REM Check if PostgreSQL is running
echo Checking PostgreSQL...
docker ps | findstr "movie-postgres" >nul
if %errorlevel% neq 0 (
    echo [WARNING] PostgreSQL is not running!
    echo Starting PostgreSQL with Docker Compose...
    docker-compose up -d postgres
    timeout /t 5 /nobreak >nul
)

echo [OK] PostgreSQL is running
echo.

REM Activate virtual environment and start backend
echo Starting Backend Server...
echo URL: http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

call .venv\Scripts\activate.bat
python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
