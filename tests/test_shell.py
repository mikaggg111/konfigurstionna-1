"""Тесты ядра эмулятора."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from shell import Shell  # noqa: E402


class ShellTest(unittest.TestCase):
    """Проверяет команды-заглушки, exit и обработку ошибок."""

    def setUp(self):
        """Создаёт новый Shell для каждого теста."""
        self.shell = Shell()

    def test_ls_stub_prints_args(self):
        """ls выводит своё имя и аргументы."""
        result = self.shell.execute("ls -l /tmp")
        self.assertEqual(result.output, "ls args: ['-l', '/tmp']")

    def test_cd_stub_prints_args(self):
        """cd выводит своё имя и аргументы."""
        self.assertEqual(self.shell.execute("cd").output, "cd args: []")

    def test_unknown_command(self):
        """Неизвестная команда даёт ошибку."""
        result = self.shell.execute("foo")
        self.assertEqual(result.error, "foo: command not found")

    def test_exit(self):
        """exit просит закрыть эмулятор."""
        self.assertTrue(self.shell.execute("exit").should_exit)

    def test_exit_with_args(self):
        """exit с аргументами даёт ошибку и не закрывает эмулятор."""
        result = self.shell.execute("exit 1")
        self.assertEqual(result.error, "exit: too many arguments")
        self.assertFalse(result.should_exit)

    def test_empty_line(self):
        """Пустой ввод ничего не делает."""
        result = self.shell.execute("   ")
        self.assertEqual((result.output, result.error), ("", ""))


if __name__ == "__main__":
    unittest.main()
