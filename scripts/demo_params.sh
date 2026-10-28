#!/bin/bash
# Демонстрация этапа 1: вывод параметров в формате ключ=значение.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo
    printf "\$ ./run.sh"; printf " %q" "$@"; echo
    ./run.sh "$@"
}

run -p requests
run --package flask --repo https://pypi.org/pypi --max-depth 3
run -p A -t -r test_repos/simple.txt -a -d 2 -f B
run -h
