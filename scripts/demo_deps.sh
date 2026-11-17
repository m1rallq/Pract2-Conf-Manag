#!/bin/bash
# Демонстрация на реальном репозитории PyPI (нужен интернет).
# Без интернета: запустите bash scripts/fake_pypi.sh во втором окне
# и передайте этому скрипту адрес: bash scripts/demo_deps.sh http://localhost:8000/pypi
cd "$(dirname "$0")/.." || exit 1
REPO="${1:-https://pypi.org/pypi}"

run() {
    echo
    printf "\$ ./run.sh"; printf " %q" "$@"; echo
    bash run.sh "$@"
}

run -p requests -r "$REPO" -d 1
run -p requests -r "$REPO"
run -p flask -r "$REPO" -d 2
run -p flask -r "$REPO" -d 2 -f jinja
run -p six -r "$REPO"
run -p no-such-package-xyz-123 -r "$REPO"
