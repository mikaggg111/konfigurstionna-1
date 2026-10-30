@echo off
rem Check all command line options of the emulator.
rem Each run opens a window: close it to go to the next test.
cd /d "%~dp0.."

echo 1. No options
python src\main.py

echo 2. VFS path only
python src\main.py --vfs vfs\minimal.csv

echo 3. Startup script only
python src\main.py --script scripts\stage2.txt

echo 4. Both options
python src\main.py --vfs vfs\minimal.csv --script scripts\stage2.txt

echo 5. Error: script does not exist
python src\main.py --script scripts\no_such_script.txt

echo 6. Help
python src\main.py --help

echo 7. Error: unknown option
python src\main.py --unknown

pause
