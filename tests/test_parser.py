"""Тесты парсера ввода."""
import unittest

from cmd_parser import parse_line


class ParserTest(unittest.TestCase):
    """Проверяет разбор строки на команду и аргументы."""

    def test_command_without_args(self):
        """Команда без аргументов."""
        parsed = parse_line("ls")
        self.assertEqual(parsed.name, "ls")
        self.assertEqual(parsed.args, [])

    def test_command_with_args(self):
        """Первое слово - команда, остальные - аргументы."""
        parsed = parse_line("cd /home user")
        self.assertEqual(parsed.name, "cd")
        self.assertEqual(parsed.args, ["/home", "user"])

    def test_extra_spaces(self):
        """Лишние пробелы игнорируются."""
        parsed = parse_line("   ls    -l   ")
        self.assertEqual(parsed.name, "ls")
        self.assertEqual(parsed.args, ["-l"])

    def test_empty_line(self):
        """Пустая строка и строка из пробелов дают None."""
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("    "))


if __name__ == "__main__":
    unittest.main()
