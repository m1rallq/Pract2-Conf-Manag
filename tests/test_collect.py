"""Тесты получения зависимостей: PyPI, тестовый репозиторий, вывод."""

import contextlib
import functools
import http.server
import io
import os
import threading
import unittest
import urllib.error

from cli import parse_args
from collector import CollectError, collect
from local_repo import LocalRepoError, parse_graph
from main import format_report, main
from pypi_client import RepositoryError, fetch_requires_dist

HERE = os.path.dirname(__file__)
FIXTURES = os.path.join(HERE, "fixtures")
REPOS = os.path.join(HERE, "..", "test_repos")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик HTTP-сервера без вывода в консоль."""

    def log_message(self, *args):
        """Не печатает журнал запросов."""


class FakePypi:
    """Локальный HTTP-сервер, отдающий сохранённые ответы PyPI."""

    def __init__(self):
        """Запускает сервер на свободном порту."""
        handler = functools.partial(QuietHandler, directory=FIXTURES)
        self.server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), handler
        )
        threading.Thread(target=self.server.serve_forever,
                         daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/pypi"

    def stop(self):
        """Останавливает сервер."""
        self.server.shutdown()
        self.server.server_close()


def failing_opener(error):
    """Возвращает функцию открытия URL, которая выбрасывает error."""
    def opener(*args, **kwargs):
        """Имитирует сетевую ошибку."""
        raise error
    return opener


class PypiTest(unittest.TestCase):
    """Получение данных через HTTP (локальный сервер вместо pypi.org)."""

    def __init__(self, method_name="runTest"):
        """Запускает свой сервер для каждого теста."""
        super().__init__(method_name)
        self.pypi = None

    def _server(self):
        """Возвращает URL запущенного тестового сервера."""
        self.pypi = FakePypi()
        self.addCleanup(self.pypi.stop)
        return self.pypi.url

    def test_requests_direct_dependencies(self):
        """У requests 4 обязательные прямые зависимости."""
        config = parse_args(["-p", "requests", "-r", self._server()])
        info = collect(config)
        self.assertEqual(info.version, "2.32.3")
        self.assertEqual([item.name for item in info.dependencies],
                         ["charset-normalizer", "idna", "urllib3",
                          "certifi"])

    def test_no_dependencies(self):
        """requires_dist = null — пакет без зависимостей."""
        config = parse_args(["-p", "six", "-r", self._server()])
        self.assertEqual(collect(config).dependencies, [])

    def test_not_found(self):
        """Несуществующий пакет — понятная ошибка."""
        config = parse_args(["-p", "nope", "-r", self._server()])
        with self.assertRaises(CollectError):
            collect(config)

    def test_connection_error(self):
        """Сетевая ошибка превращается в RepositoryError."""
        opener = failing_opener(urllib.error.URLError("offline"))
        with self.assertRaises(RepositoryError):
            fetch_requires_dist("https://pypi.org/pypi", "six", opener)

    def test_bad_json(self):
        """Ответ не в формате JSON PyPI — ошибка."""
        def opener(*args, **kwargs):
            """Возвращает HTML вместо JSON."""
            return io.BytesIO(b"<html></html>")
        with self.assertRaises(RepositoryError):
            fetch_requires_dist("https://pypi.org/pypi", "six", opener)


class LocalRepoTest(unittest.TestCase):
    """Тестовый репозиторий из файла."""

    def test_parse(self):
        """Строки файла превращаются в граф, комментарии пропускаются."""
        graph = parse_graph("# комментарий\nA: B C\nB:\nC: B # и тут\n")
        self.assertEqual(graph, {"A": ["B", "C"], "B": [], "C": ["B"]})

    def test_bad_name(self):
        """Маленькие буквы в имени — ошибка с номером строки."""
        with self.assertRaisesRegex(LocalRepoError, "строка 2"):
            parse_graph("A: B\nb: C\n")

    def test_no_colon(self):
        """Строка без двоеточия — ошибка."""
        with self.assertRaises(LocalRepoError):
            parse_graph("A B C\n")

    def test_duplicate(self):
        """Повторное описание пакета — ошибка."""
        with self.assertRaises(LocalRepoError):
            parse_graph("A: B\nA: C\n")

    def test_collect_from_file(self):
        """Прямые зависимости из файла."""
        path = os.path.join(REPOS, "simple.txt")
        info = collect(parse_args(["-p", "C", "-t", "-r", path]))
        self.assertEqual([item.name for item in info.dependencies],
                         ["D", "E"])

    def test_missing_package(self):
        """Пакета нет в файле — ошибка."""
        path = os.path.join(REPOS, "simple.txt")
        with self.assertRaises(CollectError):
            collect(parse_args(["-p", "Z", "-t", "-r", path]))

    def test_broken_file(self):
        """Ошибка в файле репозитория передаётся пользователю."""
        path = os.path.join(REPOS, "broken.txt")
        with self.assertRaises(CollectError):
            collect(parse_args(["-p", "A", "-t", "-r", path]))


class OutputTest(unittest.TestCase):
    """Вывод результата."""

    def test_report(self):
        """В отчёте есть имя, число и список зависимостей."""
        path = os.path.join(REPOS, "simple.txt")
        info = collect(parse_args(["-p", "A", "-t", "-r", path]))
        report = format_report(info)
        self.assertIn("Прямые зависимости пакета A (2)", report)
        self.assertIn("  B", report)

    def test_main_error_code(self):
        """При ошибке main возвращает 1."""
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["-p", "A", "-t"]), 1)


if __name__ == "__main__":
    unittest.main()
