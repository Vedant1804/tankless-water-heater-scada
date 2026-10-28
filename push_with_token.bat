@echo off
TITLE Push Water Heater SCADA to GitHub
cd /d "E:\MPC project\7th sem project\Burner Project"

echo ===============================================================================
echo   Push SCADA Dashboard to GitHub (Vedant1804/tankless-water-heater-scada)
echo ===============================================================================
echo.
echo Current Working Directory: %CD%
echo.

set /p TOKEN="Paste your GitHub Personal Access Token here and press Enter: "

if "%TOKEN%"=="" (
    echo [ERROR] No token provided.
    pause
    exit /b
)

echo.
echo [INFO] Uploading files to GitHub repository...
git push https://%TOKEN%@github.com/Vedant1804/tankless-water-heater-scada.git main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===============================================================================
    echo   SUCCESS! Your project has been uploaded to GitHub!
    echo   View online: https://github.com/Vedant1804/tankless-water-heater-scada
    echo ===============================================================================
) else (
    echo.
    echo ===============================================================================
    echo   Push failed. Please verify your token has 'repo' permission.
    echo ===============================================================================
)
echo.
pause
