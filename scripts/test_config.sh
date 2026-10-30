#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo "1. Без параметров"
python3 src/main.py

echo "2. Только путь к VFS"
python3 src/main.py --vfs vfs/minimal.csv

echo "3. Только стартовый скрипт"
python3 src/main.py --script scripts/stage2.txt

echo "4. Оба параметра"
python3 src/main.py --vfs vfs/minimal.csv --script scripts/stage2.txt

echo "5. Ошибка: скрипт не существует"
python3 src/main.py --script scripts/no_such_script.txt

echo "6. Справка по параметрам"
python3 src/main.py --help

echo "7. Ошибка: неизвестный параметр"
python3 src/main.py --unknown
