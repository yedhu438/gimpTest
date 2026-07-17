@echo off
cd /d C:\gimpTest
"C:\Users\VARHeist\AppData\Local\Programs\Python\Python314\python.exe" -u "C:\gimpTest\batch_processor.py" --daemon --date-after 2026-07-10 >> "C:\gimpTest\daemon.log" 2>&1
