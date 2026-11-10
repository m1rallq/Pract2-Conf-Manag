"""Получение метаданных пакета из репозитория PyPI.

Используется JSON API репозитория: ``<URL>/<пакет>/json``, например
https://pypi.org/pypi/requests/json. Зависимости лежат в поле
``info.requires_dist``. Сторонние библиотеки и pip не используются —
только стандартные модули urllib и json.
"""

import json
import urllib.error
import urllib.request

TIMEOUT_SECONDS = 15
HTTP_NOT_FOUND = 404
USER_AGENT = "depviz/0.2 (educational project)"


class RepositoryError(Exception):
    """Не удалось получить данные о пакете из репозитория."""


def package_url(repo_url, package):
    """Строит адрес JSON-описания пакета."""
    return f"{repo_url.rstrip('/')}/{package}/json"


def _download(url, opener):
    """Скачивает данные по адресу и возвращает байты."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RepositoryError(
                f"пакет не найден в репозитории ({url})"
            ) from error
        raise RepositoryError(
            f"репозиторий вернул ошибку HTTP {error.code} ({url})"
        ) from error
    except (urllib.error.URLError, OSError) as error:
        raise RepositoryError(
            f"не удалось подключиться к репозиторию ({url}): {error}"
        ) from error


def fetch_requires_dist(repo_url, package, opener=urllib.request.urlopen):
    """Возвращает версию пакета и список строк ``requires_dist``.

    Args:
        repo_url: базовый URL репозитория, например https://pypi.org/pypi.
        package: имя пакета.
        opener: функция открытия URL (подменяется в тестах).

    Raises:
        RepositoryError: при сетевой ошибке или неверном ответе.
    """
    url = package_url(repo_url, package)
    raw = _download(url, opener)
    try:
        info = json.loads(raw.decode("utf-8"))["info"]
    except (ValueError, KeyError, TypeError) as error:
        raise RepositoryError(
            f"ответ репозитория не похож на JSON PyPI ({url})"
        ) from error
    return info.get("version", ""), info.get("requires_dist") or []
