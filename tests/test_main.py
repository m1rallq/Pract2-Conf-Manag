"""Тесты точки входа: вывод параметров и код выхода."""

import contextlib
import io
import unittest

from main import main


def run_main(argv):
    """Запускает main и возвращает (код выхода, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка вывода программы."""

    def test_prints_all_params(self):
        """Все шесть параметров выводятся в формате ключ=значение."""
        code, out, _err = run_main(["-p", "requests", "-a", "-f", "test"])
        self.assertEqual(code, 0)
        for key in ("package", "repo", "test_mode", "ascii_tree",
                    "max_depth", "filter"):
            self.assertIn(f"{key}=", out)
        self.assertIn("ascii_tree=True", out)
        self.assertIn("filter=test", out)

    def test_error_code(self):
        """При ошибке в параметрах печатается сообщение и код 1."""
        code, out, err = run_main(["-p", "bad name!"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("ошибка", err)


if __name__ == "__main__":
    unittest.main()
