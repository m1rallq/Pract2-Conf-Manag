"""Точка входа: разбор параметров и вывод их в формате ключ=значение.

Пример запуска::

    python src/main.py --package requests --max-depth 3
"""

import sys

from cli import ConfigError, parse_args

EXIT_ERROR = 1


def main(argv=None):
    """Разбирает параметры и печатает их в формате ключ=значение."""
    try:
        config = parse_args(argv)
    except ConfigError as error:
        print(f"ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(config.dump())
    return 0


if __name__ == "__main__":
    sys.exit(main())
