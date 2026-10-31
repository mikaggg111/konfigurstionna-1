#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo "1. Минимальная VFS (один файл)"
python3 src/main.py --vfs vfs/minimal.csv --script scripts/stage3.txt

echo "2. VFS с несколькими файлами"
python3 src/main.py --vfs vfs/several.csv --script scripts/stage3.txt

echo "3. VFS с тремя и более уровнями файлов и папок"
python3 src/main.py --vfs vfs/deep.csv --script scripts/stage3.txt

echo "4. Без VFS (пустая)"
python3 src/main.py --script scripts/stage3.txt

echo "5. Ошибка: файл VFS не найден"
python3 src/main.py --vfs vfs/no_such_file.csv

echo "6. Ошибка: вместо файла указана папка"
python3 src/main.py --vfs vfs

echo "7. Ошибка: нет нужных столбцов"
python3 src/main.py --vfs vfs/broken/bad_columns.csv

echo "8. Ошибка: неизвестный тип записи"
python3 src/main.py --vfs vfs/broken/bad_type.csv

echo "9. Ошибка: содержимое не в base64"
python3 src/main.py --vfs vfs/broken/bad_base64.csv
