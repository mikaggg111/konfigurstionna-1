@echo off
rem Start the emulator. All arguments are passed to the program.
cd /d "%~dp0"
python src\main.py %*
