"""Тесты ядра эмулятора: диспетчер команд, exit, clear, vfsinfo."""
import unittest

from shell import Shell
from vfs import Vfs


class ShellTest(unittest.TestCase):
    """Проверяет выполнение команд."""

    def setUp(self):
        """Создаёт новый интерпретатор для каждого теста."""
        self.shell = Shell()

    def test_unknown_command(self):
        """Неизвестная команда даёт ошибку."""
        result = self.shell.execute("foo bar")
        self.assertEqual(result.error, "foo: command not found")
        self.assertFalse(result.should_exit)

    def test_empty_input(self):
        """Пустой ввод ничего не делает."""
        result = self.shell.execute("   ")
        self.assertEqual((result.output, result.error), ("", ""))

    def test_exit(self):
        """exit завершает работу."""
        self.assertTrue(self.shell.execute("exit").should_exit)

    def test_exit_with_args(self):
        """exit с аргументами - ошибка, выхода нет."""
        result = self.shell.execute("exit now")
        self.assertEqual(result.error, "exit: too many arguments")
        self.assertFalse(result.should_exit)

    def test_clear(self):
        """clear просит окно очистить экран."""
        result = self.shell.execute("clear")
        self.assertTrue(result.clear)
        self.assertEqual((result.output, result.error), ("", ""))

    def test_clear_with_args(self):
        """clear с аргументами - ошибка."""
        result = self.shell.execute("clear all")
        self.assertEqual(result.error, "clear: too many arguments")
        self.assertFalse(result.clear)

    def test_vfsinfo_empty(self):
        """vfsinfo без VFS показывает пустую VFS default."""
        result = self.shell.execute("vfsinfo")
        self.assertEqual(result.output, "VFS: default, папок: 0, файлов: 0")

    def test_vfsinfo_loaded(self):
        """vfsinfo показывает имя и размеры загруженной VFS."""
        vfs = Vfs(name="demo.csv")
        vfs.make_dirs(["a"])
        result = Shell(vfs).execute("vfsinfo")
        self.assertEqual(result.output, "VFS: demo.csv, папок: 1, файлов: 0")

    def test_vfsinfo_with_args(self):
        """vfsinfo с аргументами - ошибка."""
        result = self.shell.execute("vfsinfo x")
        self.assertEqual(result.error, "vfsinfo: too many arguments")

    def test_command_errors_get_command_name(self):
        """Ошибка команды начинается с её имени, как в UNIX."""
        result = self.shell.execute("cd /nope")
        self.assertEqual(
            result.error, "cd: /nope: No such file or directory")


if __name__ == "__main__":
    unittest.main()
