"""Тесты построения графа: BFS, глубина, фильтр, циклы, источники."""

import contextlib
import io
import os
import unittest

from cli import parse_args
from collector import CollectError, collect_graph
from graph import GraphError, build_graph, find_cycles, is_filtered
from main import main
from report import format_graph
from tests.test_collect import FakePypi

HERE = os.path.dirname(__file__)
REPOS = os.path.join(HERE, "..", "test_repos")


def repo_graph(name, package="A", *options):
    """Строит граф пакета из файла test_repos/<name>.txt."""
    path = os.path.join(REPOS, f"{name}.txt")
    return collect_graph(parse_args(["-p", package, "-t", "-r", path,
                                     *options]))


def from_dict(data):
    """Функция прямых зависимостей по словарю (для чистых тестов BFS)."""
    def direct(name):
        """Возвращает зависимости или ошибку, если пакета нет."""
        if name not in data:
            raise GraphError(f"нет пакета {name}")
        return data[name]
    return direct


class BfsTest(unittest.TestCase):
    """Обход в ширину и транзитивные зависимости."""

    def test_transitive(self):
        """В граф попадают зависимости зависимостей."""
        graph = repo_graph("simple")
        self.assertEqual(set(graph.depth), {"A", "B", "C", "D", "E"})
        self.assertEqual(graph.edges["C"], ["D", "E"])

    def test_bfs_order_and_depth(self):
        """Порядок обхода — по слоям, D найден на глубине 2 один раз."""
        graph = repo_graph("simple")
        self.assertEqual(list(graph.depth), ["A", "B", "C", "D", "E"])
        self.assertEqual(graph.depth["D"], 2)

    def test_edge_count(self):
        """Количество связей в simple.txt равно 5."""
        self.assertEqual(repo_graph("simple").edge_count, 5)

    def test_root_error(self):
        """Если корневого пакета нет — ошибка."""
        with self.assertRaises(GraphError):
            build_graph("Z", from_dict({}), 10)

    def test_missing_dependency_is_reported(self):
        """Неописанная зависимость не прерывает обход, а помечается."""
        graph = repo_graph("missing")
        self.assertIn("Z", graph.errors)
        self.assertIn("C", graph.depth)


class DepthTest(unittest.TestCase):
    """Ограничение глубины."""

    def test_depth_one_is_direct(self):
        """Глубина 1 — только прямые зависимости."""
        graph = repo_graph("deep", "A", "-d", "1")
        self.assertEqual(list(graph.depth), ["A", "B"])
        self.assertEqual(graph.unexpanded, ["B"])

    def test_depth_three(self):
        """Глубина 3 — пакеты до D включительно."""
        graph = repo_graph("deep", "A", "-d", "3")
        self.assertEqual(list(graph.depth), ["A", "B", "C", "D"])
        self.assertNotIn("D", graph.edges)

    def test_big_depth(self):
        """Большая глубина — вся цепочка, ничего не обрезано."""
        graph = repo_graph("deep", "A", "-d", "100")
        self.assertEqual(len(graph.depth), 6)
        self.assertEqual(graph.unexpanded, [])


class FilterTest(unittest.TestCase):
    """Исключение пакетов по подстроке."""

    def test_filtered_not_in_graph(self):
        """Пакеты с X в имени и их зависимости не учитываются."""
        graph = repo_graph("filter", "A", "-f", "X")
        self.assertNotIn("XB", graph.depth)
        self.assertNotIn("E", graph.depth)
        self.assertEqual(graph.filtered, ["XB", "XD"])

    def test_without_filter(self):
        """Без фильтра E достижим через XB."""
        self.assertIn("E", repo_graph("filter").depth)

    def test_case_insensitive(self):
        """Фильтр не зависит от регистра."""
        self.assertTrue(is_filtered("Charset-Normalizer", "charset"))
        self.assertFalse(is_filtered("idna", None))


class CycleTest(unittest.TestCase):
    """Циклические зависимости."""

    def test_cycle_found(self):
        """Цикл A -> B -> C -> A найден, обход завершился."""
        graph = repo_graph("cycle")
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(len(graph.depth), 4)

    def test_self_loop_and_pair(self):
        """Петля A -> A и цикл B <-> C."""
        graph = repo_graph("self_loop")
        self.assertIn(["A", "A"], graph.cycles)
        self.assertIn(["B", "C", "B"], graph.cycles)

    def test_no_cycles(self):
        """В графе без циклов ничего не найдено."""
        self.assertEqual(find_cycles({"A": ["B"], "B": []}), [])

    def test_cycle_not_counted_twice(self):
        """Один цикл с разных стартовых вершин — одна запись."""
        cycles = find_cycles({"A": ["B"], "B": ["A"], "C": ["A"]})
        self.assertEqual(cycles, [["A", "B", "A"]])


class SourceTest(unittest.TestCase):
    """Источники данных и вывод."""

    def test_pypi_graph(self):
        """Граф requests строится по HTTP, extras не попадают."""
        pypi = FakePypi()
        self.addCleanup(pypi.stop)
        graph = collect_graph(parse_args(["-p", "requests",
                                          "-r", pypi.url]))
        self.assertEqual(graph.edges["requests"],
                         ["charset-normalizer", "idna", "urllib3",
                          "certifi"])
        self.assertEqual(graph.edges["urllib3"], [])
        self.assertNotIn("pysocks", graph.depth)

    def test_broken_file(self):
        """Ошибка в файле репозитория — CollectError."""
        with self.assertRaises(CollectError):
            repo_graph("broken")

    def test_report_text(self):
        """В отчёте есть уровни, связи, циклы и итог."""
        graph = repo_graph("cycle")
        report = format_graph(graph)
        self.assertIn("уровень 1: B", report)
        self.assertIn("A -> B -> C -> A", report)
        self.assertIn("пакетов 4", report)

    def test_main_missing_root(self):
        """Нет корневого пакета в файле — код 1."""
        path = os.path.join(REPOS, "simple.txt")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["-p", "Z", "-t", "-r", path]), 1)


if __name__ == "__main__":
    unittest.main()
