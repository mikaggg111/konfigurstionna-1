@echo off
rem Check emulator commands on vfs\deep.csv.
rem Each run opens a window: close it to go to the next test.
cd /d "%~dp0.."

echo 1. Stage 4 startup script: ls, cd, tac, clear, uptime
python src\main.py --vfs vfs\deep.csv --script scripts\stage4.txt

echo 2. Command errors: one script per error
for %%f in (scripts\errors\*.txt) do (
    echo    %%f
    python src\main.py --vfs vfs\deep.csv --script %%f
)

pause
