"""Сбор прямых зависимостей пакета из выбранного источника."""

from dataclasses import dataclass, field
from typing import List

from local_repo import LocalRepoError, load_graph
from pypi_client import RepositoryError, fetch_requires_dist
from requirements import Dependency, RequirementError, direct_dependencies


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
