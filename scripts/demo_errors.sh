#!/bin/bash
# Демонстрация обработки ошибок для всех параметров.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo
    printf "\$ ./run.sh"; printf " %q" "$@"; echo
    ./run.sh "$@"
    echo "(код выхода: $?)"
}

echo "=== --package ==="
run
run -p ""
run -p "bad name!"
run -p a -t -r test_repos/simple.txt

echo "=== --repo ==="
run -p requests -r ftp://example.com
run -p requests -r test_repos/simple.txt

echo "=== --test-mode ==="
run -p A -t
run -p A -t -r no_such_file.txt

echo "=== --ascii-tree ==="
run -p requests --ascii-tree=yes

echo "=== --max-depth ==="
run -p requests -d abc
run -p requests -d 0

echo "=== --filter ==="
run -p requests -f ""

echo "=== неизвестный параметр ==="
run -p requests --color
