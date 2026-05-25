@echo off
title Varsany Automation
echo Starting Varsany Automation Daemon...
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
py run_loop.py --nas
pause
