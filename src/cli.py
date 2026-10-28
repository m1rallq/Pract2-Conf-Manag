"""Параметры командной строки и их проверка."""

import argparse
import os
import re
from dataclasses import dataclass
from typing import Optional

DEFAULT_REPO_URL = "https://pypi.org/pypi"
DEFAULT_MAX_DEPTH = 10
MIN_DEPTH = 1
URL_PREFIXES = ("http://", "https://")
PACKAGE_NAME = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE
)
TEST_PACKAGE_NAME = re.compile(r"^[A-Z]+$")


class ConfigError(Exception):
    """Ошибка в параметрах командной строки."""


@dataclass
class Config:
    """Настройки, заданные пользователем.

    Attributes:
        package: имя анализируемого пакета.
        repo: URL-адрес репозитория или путь к файлу тестового репозитория.
        test_mode: True, если repo — файл тестового репозитория.
        ascii_tree: True, если зависимости выводятся ASCII-деревом.
        max_depth: максимальная глубина анализа зависимостей.
        name_filter: подстрока для фильтрации пакетов (или None).
    """

    package: str
    repo: str
    test_mode: bool
    ascii_tree: bool
    max_depth: int
    name_filter: Optional[str]

    def as_pairs(self):
        """Возвращает параметры как список пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repo", self.repo),
            ("test_mode", self.test_mode),
            ("ascii_tree", self.ascii_tree),
            ("max_depth", self.max_depth),
            ("filter", self.name_filter or ""),
        ]

    def dump(self):
        """Возвращает параметры в формате ``ключ=значение`` по строкам."""
        return "\n".join(f"{key}={value}" for key, value in self.as_pairs())


def positive_int(text):
    """Преобразует текст в целое число не меньше MIN_DEPTH."""
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"ожидается целое число, получено '{text}'"
        ) from error
    if value < MIN_DEPTH:
        raise argparse.ArgumentTypeError(
            f"глубина должна быть не меньше {MIN_DEPTH}, получено {value}"
        )
    return value


def build_arg_parser():
    """Создаёт разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализатор графа зависимостей пакетов Python (pip)",
    )
    parser.add_argument("-p", "--package", required=True,
                        help="имя анализируемого пакета")
    parser.add_argument("-r", "--repo", default=None,
                        help="URL репозитория или путь к файлу тестового "
                             f"репозитория (по умолчанию {DEFAULT_REPO_URL})")
    parser.add_argument("-t", "--test-mode", action="store_true",
                        help="работать с тестовым репозиторием (файлом)")
    parser.add_argument("-a", "--ascii-tree", action="store_true",
                        help="выводить зависимости ASCII-деревом")
    parser.add_argument("-d", "--max-depth", type=positive_int,
                        default=DEFAULT_MAX_DEPTH,
                        help="максимальная глубина анализа "
                             f"(по умолчанию {DEFAULT_MAX_DEPTH})")
    parser.add_argument("-f", "--filter", dest="name_filter",
                        metavar="SUBSTRING", default=None,
                        help="не учитывать пакеты, имя которых "
                             "содержит эту подстроку")
    return parser


def check_package(package, test_mode):
    """Проверяет имя пакета."""
    if not package.strip():
        raise ConfigError("имя пакета не может быть пустым")
    if test_mode and not TEST_PACKAGE_NAME.match(package):
        raise ConfigError(
            "в тестовом режиме имя пакета — большие латинские буквы "
            f"(например, A), получено '{package}'"
        )
    if not PACKAGE_NAME.match(package):
        raise ConfigError(f"недопустимое имя пакета '{package}'")


def check_repo(repo, test_mode):
    """Проверяет URL репозитория или путь к тестовому файлу."""
    if test_mode:
        if repo is None:
            raise ConfigError("в тестовом режиме нужно указать --repo "
                              "с путём к файлу тестового репозитория")
        if not os.path.isfile(repo):
            raise ConfigError(f"файл тестового репозитория не найден: "
                              f"'{repo}'")
        return
    if not repo.startswith(URL_PREFIXES):
        raise ConfigError(f"URL репозитория должен начинаться с http:// "
                          f"или https://, получено '{repo}' (для файла "
                          "используйте --test-mode)")


def check_filter(text):
    """Проверяет подстроку фильтрации."""
    if text is not None and not text.strip():
        raise ConfigError("подстрока фильтра не может быть пустой")


def parse_args(argv=None):
    """Разбирает и проверяет аргументы, возвращает Config.

    Raises:
        ConfigError: если параметры заданы неверно.
        SystemExit: если argparse не смог разобрать аргументы.
    """
    args = build_arg_parser().parse_args(argv)
    repo = args.repo
    if repo is None and not args.test_mode:
        repo = DEFAULT_REPO_URL
    check_package(args.package, args.test_mode)
    check_repo(repo, args.test_mode)
    check_filter(args.name_filter)
    return Config(
        package=args.package,
        repo=repo,
        test_mode=args.test_mode,
        ascii_tree=args.ascii_tree,
        max_depth=args.max_depth,
        name_filter=args.name_filter,
    )
