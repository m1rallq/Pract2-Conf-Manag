#!/bin/bash
# Запуск программы: ./run.sh -p ПАКЕТ [параметры]
# Запуск тестов:    ./run.sh test
cd "$(dirname "$0")" || exit 1

# Ищем работающий Python. Заглушка Windows из Microsoft Store
# (WindowsApps\python.exe) не проходит проверку и пропускается.
PYTHON=""
for candidate in python3 python py; do
    if "$candidate" -c "import sys" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "ошибка: не найден Python 3. Установите его с python.org" \
         "и отметьте 'Add python.exe to PATH'." >&2
    exit 1
fi

if [ "$1" = "test" ]; then
    "$PYTHON" -m unittest discover -s tests -t . -v
else
    "$PYTHON" src/main.py "$@"
fi
