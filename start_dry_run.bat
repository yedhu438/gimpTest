@echo off
title Varsany Automation - DRY RUN
echo DRY RUN MODE - No files will be written, no DB updates
echo.
cd /d "%~dp0"
py run_loop.py --dry-run --interval 10 --nas
pause
