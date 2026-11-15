@echo off
cd /d "C:\Users\venkat\.gemini\antigravity\scratch\viral_shorts_production"
echo ========================================================
echo   Pushing 4 Multi-Scene 60FPS Shorts to GitHub Pages...
echo ========================================================
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   Deployment Pushed Successfully!
    echo   Live Web App: https://venkat1802901.github.io/cinepulse-shorts/
    echo ========================================================
) else (
    echo.
    echo [ERROR] Git push failed. Please check credentials or network.
)
pause
