"""Получение зависимостей из выбранного источника и построение графа."""

from dataclasses import dataclass, field
from typing import List

from graph import GraphError, build_graph
from local_repo import LocalRepoError, load_graph
from pypi_client import RepositoryError, fetch_requires_dist
from requirements import (
    Dependency,
    RequirementError,
    direct_dependencies,
    normalize_name,
)


class CollectError(Exception):
    """Не удалось получить зависимости пакета."""


@dataclass
class PackageInfo:
    """Пакет и его прямые зависимости.

    Attributes:
        name: имя пакета.
        version: версия пакета (пустая для тестового репозитория).
        dependencies: список прямых зависимостей.
    """

    name: str
    version: str = ""
    dependencies: List[Dependency] = field(default_factory=list)


def collect_from_pypi(config, opener=None):
    """Получает прямые зависимости пакета из репозитория PyPI."""
    kwargs = {"opener": opener} if opener else {}
    try:
        version, requires = fetch_requires_dist(
            config.repo, config.package, **kwargs
        )
        dependencies = direct_dependencies(requires)
    except (RepositoryError, RequirementError) as error:
        raise CollectError(str(error)) from error
    return PackageInfo(config.package, version, dependencies)


def collect_from_file(config):
    """Получает прямые зависимости пакета из тестового репозитория."""
    try:
        graph = load_graph(config.repo)
    except LocalRepoError as error:
        raise CollectError(f"тестовый репозиторий: {error}") from error
    if config.package not in graph:
        raise CollectError(
            f"пакет {config.package} не найден в тестовом репозитории"
        )
    dependencies = [Dependency(name) for name in graph[config.package]]
    return PackageInfo(config.package, "", dependencies)


def collect(config, opener=None):
    """Выбирает источник по режиму работы и возвращает PackageInfo.

    Raises:
        CollectError: если данные получить не удалось.
    """
    if config.test_mode:
        return collect_from_file(config)
    return collect_from_pypi(config, opener)


def pypi_source(config, opener=None):
    """Возвращает функцию «пакет -> прямые зависимости» для PyPI.

    Ответы запоминаются, чтобы каждый пакет запрашивался один раз.
    """
    cache = {}
    kwargs = {"opener": opener} if opener else {}

    def direct(name):
        """Прямые зависимости пакета name из репозитория PyPI."""
        if name not in cache:
            try:
                _version, requires = fetch_requires_dist(
                    config.repo, name, **kwargs
                )
                cache[name] = [item.name
                               for item in direct_dependencies(requires)]
            except (RepositoryError, RequirementError) as error:
                raise GraphError(str(error)) from error
        return cache[name]

    return direct


def file_source(config):
    """Возвращает функцию «пакет -> прямые зависимости» для файла.

    Raises:
        CollectError: если файл тестового репозитория содержит ошибки.
    """
    try:
        graph = load_graph(config.repo)
    except LocalRepoError as error:
        raise CollectError(f"тестовый репозиторий: {error}") from error

    def direct(name):
        """Прямые зависимости пакета name из тестового репозитория."""
        if name not in graph:
            raise GraphError(
                f"пакет {name} не найден в тестовом репозитории"
            )
        return graph[name]

    return direct


def collect_graph(config, opener=None):
    """Строит граф зависимостей пакета из выбранного источника.

    Raises:
        CollectError: если не удалось получить данные анализируемого пакета.
    """
    if config.test_mode:
        root = config.package
        direct = file_source(config)
    else:
        root = normalize_name(config.package)
        direct = pypi_source(config, opener)
    try:
        return build_graph(root, direct, config.max_depth,
                           config.name_filter)
    except GraphError as error:
        raise CollectError(str(error)) from error
