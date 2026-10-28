@echo off
TITLE Tankless Water Heater SCADA HMI Dashboard
echo ===============================================================================
echo   Starting Tankless Gas Water Heater Industrial SCADA Monitoring Dashboard
echo ===============================================================================
echo.

cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    echo Activating Virtual Environment (.venv)...
    call .venv\Scripts\activate.bat
    python -m streamlit run app.py
) ELSE (
    echo [INFO] Virtual environment not detected. Launching via Python 3.12...
    "C:\Users\ramj2\AppData\Local\Programs\Python\Python312\python.exe" -m streamlit run app.py
)

pause
