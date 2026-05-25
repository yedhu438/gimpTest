@echo off
title Varsany - First Time Setup
echo Installing Python dependencies...
cd /d "%~dp0"
py -m pip install -r requirements.txt
echo.
echo Testing database connection...
py db.py
echo.
echo Setup complete. Double-click start.bat to run.
pause
