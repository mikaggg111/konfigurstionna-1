"""Тесты парсера ввода."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cmd_parser import parse_line


class ParserTest(unittest.TestCase):
    """Проверяет разбор строки на команду и аргументы."""

    def test_command_with_args(self):
        """Первое слово - команда, остальные - аргументы."""
        parsed = parse_line("ls -l /tmp")
        self.assertEqual(parsed.name, "ls")
        self.assertEqual(parsed.args, ["-l", "/tmp"])

    def test_extra_spaces(self):
        """Лишние пробелы игнорируются."""
        parsed = parse_line("   ls    a   b  ")
        self.assertEqual(parsed.name, "ls")
        self.assertEqual(parsed.args, ["a", "b"])

    def test_no_args(self):
        """Команда без аргументов даёт пустой список."""
        self.assertEqual(parse_line("cd").args, [])

    def test_empty_line(self):
        """Пустая строка и пробелы дают None."""
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("    "))


if __name__ == "__main__":
    unittest.main()
