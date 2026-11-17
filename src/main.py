"""Точка входа: построение и вывод графа зависимостей пакета.

Пример запуска::

    python src/main.py --package requests --max-depth 2
    python src/main.py -p A -t -r test_repos/simple.txt -f E
"""

import sys

from cli import ConfigError, parse_args
from collector import CollectError, collect_graph
from report import format_graph

EXIT_ERROR = 1


def main(argv=None):
    """Разбирает параметры, строит граф зависимостей и печатает его."""
    try:
        config = parse_args(argv)
        graph = collect_graph(config)
    except (ConfigError, CollectError) as error:
        print(f"ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(format_graph(graph, config.name_filter))
    return 0


if __name__ == "__main__":
    sys.exit(main())
