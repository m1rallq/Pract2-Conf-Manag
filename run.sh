#!/bin/bash
# Запуск программы: ./run.sh -p ПАКЕТ [параметры]
# Запуск тестов:    ./run.sh test
cd "$(dirname "$0")" || exit 1
PYTHON=python3
command -v python >/dev/null 2>&1 && PYTHON=python

if [ "$1" = "test" ]; then
    "$PYTHON" -m unittest discover -s tests -t . -v
else
    "$PYTHON" src/main.py "$@"
fi
