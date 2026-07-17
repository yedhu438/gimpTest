@echo off
:loop
rclone copy "C:\gimpTest\Output" b2varsany:varsaniautomation --log-file="C:\gimpTest\rclone_sync.log" --log-level INFO
timeout /t 5 /nobreak
goto loop
