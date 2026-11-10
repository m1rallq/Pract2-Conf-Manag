"""Разбор строк зависимостей пакетов Python (формат PEP 508).

Пример строки из поля ``requires_dist`` метаданных пакета::

    PySocks!=1.5.7,>=1.5.6; extra == "socks"

Здесь ``PySocks`` — имя, ``!=1.5.7,>=1.5.6`` — ограничение версии,
``extra == "socks"`` — маркер (условие установки).
"""

import re
from dataclasses import dataclass

NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
EXTRAS_PATTERN = re.compile(r"^\s*\[[^\]]*\]")
EXTRA_MARKER = re.compile(r"\bextra\s*==")
NAME_SEPARATORS = re.compile(r"[-_.]+")


class RequirementError(Exception):
    """Строку зависимости не удалось разобрать."""


@dataclass
class Dependency:
    """Одна зависимость пакета.

    Attributes:
        name: нормализованное имя пакета.
        specifier: ограничение версии, например ``>=2,<4`` (может быть пустым).
        marker: условие установки, например ``python_version < "3.10"``.
    """

    name: str
    specifier: str = ""
    marker: str = ""

    @property
    def is_optional(self):
        """True, если зависимость нужна только для доп. возможности (extra)."""
        return bool(EXTRA_MARKER.search(self.marker))


def normalize_name(name):
    """Приводит имя пакета к единому виду (PEP 503).

    Пример: ``Charset_Normalizer`` -> ``charset-normalizer``.
    """
    return NAME_SEPARATORS.sub("-", name).lower()


def parse_requirement(line):
    """Разбирает одну строку зависимости в объект Dependency.

    Raises:
        RequirementError: если в строке нет имени пакета.
    """
    requirement, marker = (line.split(";", 1) + [""])[:2]
    match = NAME_PATTERN.match(requirement)
    if not match:
        raise RequirementError(f"не удалось разобрать зависимость '{line}'")
    rest = requirement[match.end():]
    rest = EXTRAS_PATTERN.sub("", rest).strip()
    specifier = rest.strip("()").replace(" ", "")
    return Dependency(
        name=normalize_name(match.group(1)),
        specifier=specifier,
        marker=marker.strip(),
    )


def direct_dependencies(requires_dist):
    """Возвращает обязательные прямые зависимости без повторов.

    Зависимости с маркером ``extra == ...`` пропускаются: pip ставит их
    только по явному запросу (``pip install pkg[extra]``).
    """
    result = []
    seen = set()
    for line in requires_dist or []:
        dependency = parse_requirement(line)
        if dependency.is_optional or dependency.name in seen:
            continue
        seen.add(dependency.name)
        result.append(dependency)
    return result
