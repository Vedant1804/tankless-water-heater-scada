# PowerShell Launcher for Tankless Water Heater SCADA Dashboard
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "   Starting Tankless Gas Water Heater Industrial SCADA Monitoring Dashboard" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment (.venv)..." -ForegroundColor Yellow
    & ".\.venv\Scripts\Activate.ps1"
    python -m streamlit run app.py
} else {
    Write-Host "[INFO] Virtual environment not found. Running with global Python 3.12..." -ForegroundColor Yellow
    & "C:\Users\ramj2\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py
}
