@echo off
TITLE Push SCADA Project to GitHub
echo ===============================================================================
echo   Pushing Water Heater Digital Twin SCADA Dashboard to GitHub
echo ===============================================================================
echo.
cd /d "%~dp0"

echo [1/3] Active Git Remote:
git remote -v
echo.

echo [2/3] Staged Commit Information:
git log -1 --oneline
echo.

echo [3/3] Initiating Push to GitHub (main branch)...
echo If a sign-in window appears, click "Sign in with your browser" to authorize.
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===============================================================================
    echo   SUCCESS: Project successfully uploaded to GitHub!
    echo ===============================================================================
) else (
    echo.
    echo [NOTE] If authentication failed, clear old credentials with:
    echo        cmdkey /delete:LegacyGeneric:target=git:https://github.com
    echo        Then re-run this script.
)
echo.
pause
