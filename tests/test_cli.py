"""Тесты разбора и проверки параметров командной строки."""

import contextlib
import io
import os
import unittest

from cli import DEFAULT_REPO_URL, ConfigError, parse_args

HERE = os.path.dirname(__file__)
SIMPLE_REPO = os.path.join(HERE, "..", "test_repos", "simple.txt")


def parse_quietly(argv):
    """Вызывает parse_args, скрывая сообщения argparse в stderr."""
    with contextlib.redirect_stderr(io.StringIO()):
        return parse_args(argv)


class ValidArgsTest(unittest.TestCase):
    """Правильные наборы параметров."""

    def test_defaults(self):
        """Без необязательных параметров берутся значения по умолчанию."""
        config = parse_args(["-p", "requests"])
        self.assertEqual(config.repo, DEFAULT_REPO_URL)
        self.assertFalse(config.test_mode)
        self.assertFalse(config.ascii_tree)
        self.assertIsNone(config.name_filter)

    def test_all_params(self):
        """Все параметры попадают в Config."""
        config = parse_args(["-p", "A", "-t", "-r", SIMPLE_REPO, "-a",
                             "-d", "3", "-f", "B"])
        self.assertTrue(config.test_mode)
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.name_filter, "B")

    def test_dump(self):
        """dump выводит параметры в формате ключ=значение."""
        dump = parse_args(["-p", "flask", "-d", "2"]).dump()
        self.assertIn("package=flask", dump)
        self.assertIn("max_depth=2", dump)
        self.assertIn(f"repo={DEFAULT_REPO_URL}", dump)

    def test_custom_url(self):
        """Можно указать свой URL репозитория."""
        config = parse_args(["-p", "six", "-r", "http://localhost/pypi"])
        self.assertEqual(config.repo, "http://localhost/pypi")


class InvalidArgsTest(unittest.TestCase):
    """Ошибки в параметрах."""

    def test_missing_package(self):
        """Имя пакета обязательно."""
        with self.assertRaises(SystemExit):
            parse_quietly([])

    def test_empty_package(self):
        """Пустое имя пакета — ошибка."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", " "])

    def test_bad_package_name(self):
        """Недопустимые символы в имени пакета — ошибка."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", "bad name!"])

    def test_bad_url(self):
        """URL без http(s) — ошибка."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", "six", "-r", "ftp://example.com"])

    def test_test_mode_without_repo(self):
        """В тестовом режиме нужен путь к файлу."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", "A", "-t"])

    def test_test_mode_missing_file(self):
        """Несуществующий файл тестового репозитория — ошибка."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", "A", "-t", "-r", "no_such_file.txt"])

    def test_test_mode_lowercase_package(self):
        """В тестовом режиме имя пакета — большие буквы."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", "a", "-t", "-r", SIMPLE_REPO])

    def test_depth_not_number(self):
        """Глубина должна быть числом."""
        with self.assertRaises(SystemExit):
            parse_quietly(["-p", "six", "-d", "abc"])

    def test_depth_zero(self):
        """Глубина должна быть не меньше 1."""
        with self.assertRaises(SystemExit):
            parse_quietly(["-p", "six", "-d", "0"])

    def test_empty_filter(self):
        """Пустая подстрока фильтра — ошибка."""
        with self.assertRaises(ConfigError):
            parse_args(["-p", "six", "-f", ""])

    def test_flag_with_value(self):
        """Флагу ASCII-дерева нельзя передать значение."""
        with self.assertRaises(SystemExit):
            parse_quietly(["-p", "six", "--ascii-tree=yes"])

    def test_unknown_option(self):
        """Неизвестный параметр — ошибка."""
        with self.assertRaises(SystemExit):
            parse_quietly(["-p", "six", "--color"])


if __name__ == "__main__":
    unittest.main()
