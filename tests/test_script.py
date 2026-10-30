"""Тесты чтения стартового скрипта."""
import os
import tempfile
import unittest

import _path
from errors import ShellError
from script import load_script


def write_temp(text, encoding="utf-8"):
    """Создаёт временный файл с текстом и возвращает его путь."""
    handle, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(handle, "w", encoding=encoding, newline="") as file:
        file.write(text)
    return path


class ScriptTest(unittest.TestCase):
    """Проверяет загрузку скрипта."""

    def load(self, text, encoding="utf-8"):
        """Загружает скрипт из текста и удаляет временный файл."""
        path = write_temp(text, encoding)
        self.addCleanup(os.remove, path)
        return load_script(path)

    def test_commands_with_line_numbers(self):
        """Возвращаются пары (номер строки, команда)."""
        self.assertEqual(self.load("ls\ncd /a\n"), [(1, "ls"), (2, "cd /a")])

    def test_comments_and_empty_lines(self):
        """Комментарии и пустые строки пропускаются, номера сохраняются."""
        text = "# заголовок\n\nls  # хвостовой комментарий\n   \n"
        self.assertEqual(self.load(text), [(3, "ls")])

    def test_windows_line_endings(self):
        """Строки с \\r\\n читаются так же, как с \\n."""
        self.assertEqual(self.load("ls\r\ncd\r\n"), [(1, "ls"), (2, "cd")])

    def test_bom_is_ignored(self):
        """Метка BOM в начале файла не мешает первой команде."""
        self.assertEqual(self.load("ls\n", "utf-8-sig"), [(1, "ls")])

    def test_missing_file(self):
        """Нет файла - ShellError."""
        with self.assertRaises(ShellError):
            load_script("no_such_script.txt")

    def test_wrong_encoding(self):
        """Файл не в UTF-8 - ShellError."""
        path = write_temp("привет", "cp1251")
        self.addCleanup(os.remove, path)
        with self.assertRaises(ShellError):
            load_script(path)


if __name__ == "__main__":
    unittest.main()
