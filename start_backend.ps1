# Start the Movie Recommendation Backend

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Movie Recommendation Backend" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if PostgreSQL is running
Write-Host "Checking PostgreSQL..." -ForegroundColor Yellow
$pgRunning = docker ps | Select-String "movie-postgres"
if (-not $pgRunning) {
    Write-Host "[WARNING] PostgreSQL is not running!" -ForegroundColor Red
    Write-Host "Starting PostgreSQL with Docker Compose..." -ForegroundColor Yellow
    docker-compose up -d postgres
    Start-Sleep -Seconds 5
}

Write-Host "[OK] PostgreSQL is running" -ForegroundColor Green
Write-Host ""

# Activate virtual environment and start backend
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
Write-Host "URL: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

& .\.venv\Scripts\Activate.ps1
python -m uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
