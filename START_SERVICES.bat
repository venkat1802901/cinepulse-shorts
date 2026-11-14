@echo off
title CinePulse Mobile App Services
echo Starting CinePulse Server & Cloudflare Tunnel...
python "%~dp0run_services.py"
pause
