@echo off
title Varsany - Update Code
echo Pulling latest code from GitHub...
cd /d "%~dp0"
git pull
echo.
echo Update complete. Restart start.bat to apply changes.
pause
