#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

echo "1. Стартовый скрипт этапа 4: ls, cd, tac, clear, uptime"
python3 src/main.py --vfs vfs/deep.csv --script scripts/stage4.txt

echo "2. Стартовый скрипт этапа 5: cp (VFS меняется только в памяти)"
python3 src/main.py --vfs vfs/deep.csv --script scripts/stage5.txt

echo "3. Ошибки команд: по одному скрипту на каждую ошибку"
for script in scripts/errors/*.txt; do
    echo "   $script"
    python3 src/main.py --vfs vfs/deep.csv --script "$script"
done
