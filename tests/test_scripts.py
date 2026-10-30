"""Тесты стартовых скриптов из папки scripts (без окна)."""
import glob
import os
import unittest

import _path
from script import load_script
from shell import Shell
from vfs import load_vfs

ROOT = os.path.join(os.path.dirname(__file__), "..")
ALL_VFS = ("minimal.csv", "several.csv", "deep.csv")


def path_of(*parts):
    """Возвращает путь внутри репозитория."""
    return os.path.join(ROOT, *parts)


def run_script(shell, path):
    """Выполняет скрипт так же, как окно: до первой ошибки.

    Возвращает (список результатов, команда с ошибкой или None).
    """
    results = []
    for _number, line in load_script(path):
        result = shell.execute(line)
        results.append(result)
        if result.error:
            return results, line
    return results, None


def shell_for(vfs_name=None):
    """Создаёт Shell с VFS из папки vfs (или пустой)."""
    if vfs_name is None:
        return Shell()
    return Shell(load_vfs(path_of("vfs", vfs_name)))


class StartupScriptsTest(unittest.TestCase):
    """Каждый скрипт должен дойти до своей ошибки."""

    def test_stage2_on_any_vfs(self):
        """Скрипт этапа 2 останавливается на exit с аргументом."""
        for name in (None,) + ALL_VFS:
            with self.subTest(vfs=name):
                _, failed = run_script(
                    shell_for(name), path_of("scripts", "stage2.txt"))
                self.assertEqual(failed, "exit now")

    def test_stage3_on_any_vfs(self):
        """Скрипт этапа 3 работает на любой VFS и ловит одну ошибку."""
        for name in (None,) + ALL_VFS:
            with self.subTest(vfs=name):
                results, failed = run_script(
                    shell_for(name), path_of("scripts", "stage3.txt"))
                self.assertEqual(failed, "vfsinfo extra")
                self.assertIn("VFS:", results[0].output)

    def test_stage4(self):
        """Скрипт этапа 4 доходит до последней ошибки и очищает экран."""
        results, failed = run_script(
            shell_for("deep.csv"), path_of("scripts", "stage4.txt"))
        self.assertEqual(failed, "tac /no/such/file.txt")
        self.assertTrue(any(result.clear for result in results))
        self.assertEqual([r.error for r in results[:-1]],
                         [""] * (len(results) - 1))

    def test_each_error_script_fails_on_its_last_command(self):
        """Скрипты из scripts/errors ошибаются только на последней строке."""
        scripts = sorted(glob.glob(path_of("scripts", "errors", "*.txt")))
        self.assertTrue(scripts)
        for path in scripts:
            with self.subTest(script=os.path.basename(path)):
                lines = [line for _, line in load_script(path)]
                results, failed = run_script(shell_for("deep.csv"), path)
                self.assertEqual(failed, lines[-1])
                self.assertEqual(len(results), len(lines))


if __name__ == "__main__":
    unittest.main()
