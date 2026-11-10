"""Точка входа: вывод прямых зависимостей пакета.

Пример запуска::

    python src/main.py --package requests
    python src/main.py -p A -t -r test_repos/simple.txt
"""

import sys

from cli import ConfigError, parse_args
from collector import CollectError, collect

EXIT_ERROR = 1


def format_dependency(dependency):
    """Возвращает строку для одной зависимости."""
    line = f"  {dependency.name}"
    if dependency.specifier:
        line += f" {dependency.specifier}"
    if dependency.marker:
        line += f"  (при условии: {dependency.marker})"
    return line


def format_report(info):
    """Формирует текст со списком прямых зависимостей пакета."""
    title = info.name + (f" {info.version}" if info.version else "")
    if not info.dependencies:
        return f"Пакет {title} не имеет прямых зависимостей."
    lines = [f"Прямые зависимости пакета {title} "
             f"({len(info.dependencies)}):"]
    lines += [format_dependency(item) for item in info.dependencies]
    return "\n".join(lines)


def main(argv=None):
    """Разбирает параметры, собирает и печатает прямые зависимости."""
    try:
        config = parse_args(argv)
        info = collect(config)
    except (ConfigError, CollectError) as error:
        print(f"ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(format_report(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
