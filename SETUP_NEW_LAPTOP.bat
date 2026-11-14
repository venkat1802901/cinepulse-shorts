@echo off
setlocal enabledelayedexpansion
title CinePulse Autonomous Video Production Setup
echo ================================================================
echo   🎬 CINEPULSE PRODUCTION SYSTEM — 1-CLICK LAPTOP SETUP
echo ================================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.12 (check "Add Python to PATH" during install).
    pause
    exit /b 1
)

:: Check for FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg is not found in PATH!
    echo Please install FFmpeg (e.g. winget install Gyan.FFmpeg)
)

echo [1/3] Installing Python dependencies...
python -m pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [2/3] Registering Midnight 12:00 AM Automated Task...
schtasks /create /tn "CinePulse_Daily_Production" /tr "python \"%~dp0daily_runner.py\"" /sc daily /st 00:00 /f >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$t = Get-ScheduledTask -TaskName 'CinePulse_Daily_Production'; $t.Settings.WakeToRun = $true; $t.Settings.ExecutionTimeLimit = 'PT4H'; $t.Settings.DisallowStartIfOnBatteries = $false; $t.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -InputObject $t" >nul 2>&1
echo   - Windows Task Scheduler configured: Triggers at 12:00 AM Daily
echo   - WakeToRun: ENABLED (Laptop wakes up automatically)

echo.
echo [3/3] Starting CinePulse Mobile App Server ^& Cloudflare Tunnel...
start "" python "%~dp0run_services.py"

echo.
echo ================================================================
echo   ✅ SETUP COMPLETE! 
echo   CinePulse is now fully operational on this machine.
echo   Check the opened window for your live mobile phone app URL!
echo ================================================================
echo.
pause
