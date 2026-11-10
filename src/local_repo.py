"""Тестовый репозиторий: граф пакетов, описанный в текстовом файле.

Формат файла — одна строка на пакет: имя, двоеточие, зависимости
через пробел. Имена — большие латинские буквы. ``#`` — комментарий::

    # A зависит от B и C
    A: B C
    B: C
    C:
"""

import re

PACKAGE_NAME = re.compile(r"^[A-Z]+$")
COMMENT = "#"


class LocalRepoError(Exception):
    """Ошибка в файле тестового репозитория."""


def _check_name(name, number):
    """Проверяет имя пакета в строке с номером number."""
    if not PACKAGE_NAME.match(name):
        raise LocalRepoError(
            f"строка {number}: имя пакета '{name}' должно состоять "
            "из больших латинских букв"
        )


def _parse_line(line, number):
    """Разбирает строку ``A: B C`` в пару (A, [B, C])."""
    name, colon, rest = line.partition(":")
    if not colon:
        raise LocalRepoError(
            f"строка {number}: ожидается формат 'ПАКЕТ: ЗАВИСИМОСТИ'"
        )
    name = name.strip()
    dependencies = rest.split()
    for item in [name] + dependencies:
        _check_name(item, number)
    return name, dependencies


def parse_graph(text):
    """Разбирает текст тестового репозитория в словарь {пакет: [зависимости]}.

    Raises:
        LocalRepoError: при ошибке формата или повторе пакета.
    """
    graph = {}
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        name, dependencies = _parse_line(line, number)
        if name in graph:
            raise LocalRepoError(f"строка {number}: пакет {name} "
                                "описан повторно")
        graph[name] = dependencies
    return graph


def load_graph(path):
    """Читает файл тестового репозитория и возвращает граф.

    Raises:
        LocalRepoError: если файл не читается или содержит ошибки.
    """
    try:
        with open(path, encoding="utf-8") as file:
            text = file.read()
    except OSError as error:
        raise LocalRepoError(f"не удалось прочитать файл: {error}") from error
    return parse_graph(text)
