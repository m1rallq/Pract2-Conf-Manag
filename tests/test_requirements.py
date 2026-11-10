"""Тесты разбора строк зависимостей."""

import unittest

from requirements import (
    RequirementError,
    direct_dependencies,
    normalize_name,
    parse_requirement,
)


class ParseRequirementTest(unittest.TestCase):
    """Разбор одной строки requires_dist."""

    def test_name_and_specifier(self):
        """Имя и ограничение версии разделяются."""
        dependency = parse_requirement("idna<4,>=2.5")
        self.assertEqual(dependency.name, "idna")
        self.assertEqual(dependency.specifier, "<4,>=2.5")

    def test_name_only(self):
        """Строка без версии."""
        dependency = parse_requirement("six")
        self.assertEqual(dependency.name, "six")
        self.assertEqual(dependency.specifier, "")

    def test_marker(self):
        """Маркер после ; сохраняется."""
        dependency = parse_requirement(
            'importlib-metadata>=3.6; python_version < "3.10"'
        )
        self.assertEqual(dependency.marker, 'python_version < "3.10"')
        self.assertFalse(dependency.is_optional)

    def test_extra_is_optional(self):
        """Зависимость с extra — необязательная."""
        dependency = parse_requirement('PySocks>=1.5.6; extra == "socks"')
        self.assertTrue(dependency.is_optional)

    def test_extras_brackets(self):
        """Квадратные скобки с extras убираются."""
        dependency = parse_requirement("urllib3[socks] >= 1.26")
        self.assertEqual(dependency.name, "urllib3")
        self.assertEqual(dependency.specifier, ">=1.26")

    def test_old_style_parentheses(self):
        """Старый формат с версией в скобках."""
        self.assertEqual(parse_requirement("zope (>=4.0)").specifier, ">=4.0")

    def test_normalized_name(self):
        """Имя приводится к нижнему регистру с дефисами."""
        self.assertEqual(parse_requirement("Charset_Normalizer").name,
                         "charset-normalizer")

    def test_garbage(self):
        """Строка без имени — ошибка."""
        with self.assertRaises(RequirementError):
            parse_requirement(">=1.0")


class DirectDependenciesTest(unittest.TestCase):
    """Отбор прямых зависимостей."""

    def test_skips_extras_and_duplicates(self):
        """Extras и повторы не попадают в результат, порядок сохраняется."""
        names = [item.name for item in direct_dependencies([
            "b>=1", 'c; extra == "x"', "a", "B<2",
        ])]
        self.assertEqual(names, ["b", "a"])

    def test_none(self):
        """requires_dist = None означает отсутствие зависимостей."""
        self.assertEqual(direct_dependencies(None), [])

    def test_normalize(self):
        """Разные написания одного имени совпадают."""
        self.assertEqual(normalize_name("Zope.Interface"), "zope-interface")


if __name__ == "__main__":
    unittest.main()
