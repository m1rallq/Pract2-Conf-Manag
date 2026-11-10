#!/bin/bash
# Демонстрация этапа 2: прямые зависимости пакетов.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo
    printf "\$ ./run.sh"; printf " %q" "$@"; echo
    ./run.sh "$@"
}

echo "=== Реальный репозиторий PyPI (нужен интернет) ==="
run -p requests
run -p flask
run -p six
run -p no-such-package-xyz-123

echo
echo "=== Тестовый репозиторий (файл) ==="
run -p A -t -r test_repos/simple.txt
run -p C -t -r test_repos/cycle.txt
run -p D -t -r test_repos/simple.txt
