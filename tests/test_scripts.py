"""Тесты стартовых скриптов из папки scripts (без окна)."""
import os
import unittest

import _path
from script import load_script
from shell import Shell
from vfs import load_vfs

ROOT = os.path.join(os.path.dirname(__file__), "..")


def path_of(*parts):
    """Возвращает путь внутри репозитория."""
    return os.path.join(ROOT, *parts)


def run_script(shell, name):
    """Выполняет скрипт так же, как окно: до первой ошибки.

    Возвращает (список результатов, номер строки с ошибкой или None).
    """
    results = []
    for number, line in load_script(path_of("scripts", name)):
        result = shell.execute(line)
        results.append(result)
        if result.error:
            return results, number
    return results, None


class StartupScriptsTest(unittest.TestCase):
    """Каждый скрипт должен дойти до своей ошибки в нужной строке."""

    def shell_for(self, vfs_name):
        """Создаёт Shell с VFS из папки vfs."""
        return Shell(load_vfs(path_of("vfs", vfs_name)))

    def test_stage2_stops_on_exit_with_args(self):
        """Скрипт этапа 2 останавливается на exit с аргументом."""
        _, line = run_script(Shell(), "stage2.txt")
        self.assertEqual(line, 10)

    def test_stage3_on_every_vfs(self):
        """Скрипт этапа 3 работает на любой VFS и ловит одну ошибку."""
        for name in ("minimal.csv", "several.csv", "deep.csv"):
            with self.subTest(vfs=name):
                results, line = run_script(self.shell_for(name), "stage3.txt")
                self.assertEqual(line, 10)
                self.assertIn(name, results[0].output)

    def test_stage3_without_vfs(self):
        """Скрипт этапа 3 работает и без VFS."""
        _, line = run_script(Shell(), "stage3.txt")
        self.assertEqual(line, 10)


if __name__ == "__main__":
    unittest.main()
