"""Тесты параметров командной строки."""
import contextlib
import io
import unittest

import _path
from config import Config, parse_args


class ConfigTest(unittest.TestCase):
    """Проверяет разбор параметров и отладочный вывод."""

    def test_no_params(self):
        """Без параметров обе настройки не заданы."""
        config = parse_args([])
        self.assertIsNone(config.vfs_path)
        self.assertIsNone(config.script_path)

    def test_both_params(self):
        """Оба параметра попадают в Config."""
        config = parse_args(["--vfs", "a.csv", "--script", "s.txt"])
        self.assertEqual(config, Config("a.csv", "s.txt"))

    def test_unknown_param_exits(self):
        """Неизвестный параметр останавливает программу с ошибкой."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--unknown"])

    def test_debug_lines_show_all_params(self):
        """Отладочный вывод содержит все заданные параметры."""
        text = "\n".join(Config("a.csv", "s.txt").debug_lines())
        self.assertIn("a.csv", text)
        self.assertIn("s.txt", text)

    def test_debug_lines_not_set(self):
        """Незаданные параметры помечены как не заданные."""
        text = "\n".join(Config().debug_lines())
        self.assertEqual(text.count("<не задан>"), 2)


if __name__ == "__main__":
    unittest.main()
