#!/bin/bash
# Локальная копия PyPI на случай, если нет интернета.
# Запуск:   bash scripts/fake_pypi.sh
# Затем в другом окне: ./run.sh -p requests -r http://localhost:8000/pypi
# Остановка: Ctrl+C
cd "$(dirname "$0")/.." || exit 1
PYTHON=python3
command -v python >/dev/null 2>&1 && PYTHON=python
echo "Локальный PyPI: http://localhost:8000/pypi (пакеты: requests, flask, click, six)"
"$PYTHON" -m http.server 8000 --directory tests/fixtures
