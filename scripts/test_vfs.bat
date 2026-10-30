@echo off
rem Check the emulator with different VFS files (CSV files in vfs\).
rem Each run opens a window: close it to go to the next test.
cd /d "%~dp0.."

echo 1. Minimal VFS (one file)
python src\main.py --vfs vfs\minimal.csv --script scripts\stage3.txt

echo 2. VFS with several files
python src\main.py --vfs vfs\several.csv --script scripts\stage3.txt

echo 3. VFS with 3 or more levels of files and folders
python src\main.py --vfs vfs\deep.csv --script scripts\stage3.txt

echo 4. No VFS (empty)
python src\main.py --script scripts\stage3.txt

echo 5. Error: VFS file not found
python src\main.py --vfs vfs\no_such_file.csv

echo 6. Error: a folder instead of a file
python src\main.py --vfs vfs

echo 7. Error: required columns are missing
python src\main.py --vfs vfs\broken\bad_columns.csv

echo 8. Error: unknown record type
python src\main.py --vfs vfs\broken\bad_type.csv

echo 9. Error: content is not base64
python src\main.py --vfs vfs\broken\bad_base64.csv

pause
