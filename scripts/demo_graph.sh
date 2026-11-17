#!/bin/bash
# Демонстрация этапа 3: граф зависимостей на тестовых репозиториях.
cd "$(dirname "$0")/.." || exit 1

run() {
    echo
    echo "=================================================================="
    printf "\$ ./run.sh"; printf " %q" "$@"; echo
    echo "=================================================================="
    bash run.sh "$@"
}

echo "### 1. Транзитивные зависимости (BFS): simple.txt"
cat test_repos/simple.txt
run -p A -t -r test_repos/simple.txt

echo
echo "### 2. Ограничение глубины: deep.txt (цепочка A -> ... -> F)"
run -p A -t -r test_repos/deep.txt -d 1
run -p A -t -r test_repos/deep.txt -d 3
run -p A -t -r test_repos/deep.txt

echo
echo "### 3. Фильтр по подстроке: filter.txt"
run -p A -t -r test_repos/filter.txt
run -p A -t -r test_repos/filter.txt -f X

echo
echo "### 4. Циклические зависимости"
run -p A -t -r test_repos/cycle.txt
run -p A -t -r test_repos/self_loop.txt

echo
echo "### 5. Пакет, который не описан в репозитории"
run -p A -t -r test_repos/missing.txt

echo
echo "### 6. Другой корневой пакет"
run -p C -t -r test_repos/simple.txt
