"""Тесты команд ls, cd и tac на примере vfs/deep.csv."""
import os
import unittest

from shell import Shell
from vfs import load_vfs

DEEP = os.path.join(os.path.dirname(__file__), "..", "vfs", "deep.csv")


class CommandCase(unittest.TestCase):
    """Базовый класс: Shell с загруженной VFS deep.csv."""

    def setUp(self):
        """Загружает VFS и создаёт Shell."""
        self.shell = Shell(load_vfs(DEEP))

    def ok(self, line):
        """Выполняет команду, проверяет успех и возвращает вывод."""
        result = self.shell.execute(line)
        self.assertEqual(result.error, "")
        return result.output

    def fail(self, line):
        """Выполняет команду, проверяет ошибку и возвращает её текст."""
        result = self.shell.execute(line)
        self.assertNotEqual(result.error, "", f"'{line}' не дала ошибки")
        return result.error

    def size_of(self, path):
        """Размер файла VFS в байтах."""
        return len(self.shell.vfs.find(path).content)


class LsTest(CommandCase):
    """Команда ls."""

    def test_root(self):
        """ls без аргументов: по алфавиту, у папок слэш."""
        self.assertEqual(self.ok("ls"), "empty/  etc/  home/  readme.txt")

    def test_path(self):
        """ls с путём к папке."""
        self.assertEqual(self.ok("ls /home/user"),
                         "docs/  notes.txt  photo.bin")

    def test_relative_path(self):
        """ls с относительным путём."""
        self.shell.execute("cd /home")
        self.assertEqual(self.ok("ls user/docs"), "archive/  todo.txt")

    def test_file(self):
        """ls для файла печатает его имя как указано."""
        self.assertEqual(self.ok("ls /etc/motd"), "/etc/motd")

    def test_empty_dir(self):
        """У пустой папки нет вывода."""
        self.assertEqual(self.ok("ls /empty"), "")

    def test_long(self):
        """ls -l: тип, размер и имя."""
        size = self.size_of("/etc/motd")
        self.assertEqual(self.ok("ls -l /etc"), f"- {size:>6} motd")
        self.assertEqual(self.ok("ls -l /empty"), "")
        first = self.ok("ls -l").splitlines()[0]
        self.assertEqual(first, "d      0 empty")

    def test_multiple_paths(self):
        """Несколько папок: заголовки и пустая строка между ними."""
        self.assertEqual(self.ok("ls /etc /empty"), "/etc:\nmotd\n\n/empty:")

    def test_missing(self):
        """Нет такого пути."""
        self.assertEqual(self.fail("ls /nope"),
                         "ls: /nope: No such file or directory")

    def test_through_file(self):
        """Путь через файл."""
        self.assertIn("Not a directory", self.fail("ls /readme.txt/x"))

    def test_bad_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.fail("ls -x"), "ls: invalid option -- 'x'")


class CdTest(CommandCase):
    """Команда cd."""

    def cwd(self):
        """Текущая папка VFS."""
        return self.shell.vfs.cwd_path()

    def test_absolute_and_relative(self):
        """Абсолютный и относительный переходы."""
        self.ok("cd /home/user/docs")
        self.assertEqual(self.cwd(), "/home/user/docs")
        self.ok("cd archive/2025")
        self.assertEqual(self.cwd(), "/home/user/docs/archive/2025")

    def test_dots(self):
        """. и .. работают."""
        self.ok("cd /home/user/docs/archive")
        self.ok("cd ../..")
        self.assertEqual(self.cwd(), "/home/user")
        self.ok("cd .")
        self.assertEqual(self.cwd(), "/home/user")

    def test_above_root(self):
        """Выше корня подняться нельзя."""
        self.ok("cd /home")
        self.ok("cd ../../..")
        self.assertEqual(self.cwd(), "/")

    def test_no_args_goes_to_root(self):
        """cd без аргументов - в корень."""
        self.ok("cd /etc")
        self.ok("cd")
        self.assertEqual(self.cwd(), "/")

    def test_ls_follows_cd(self):
        """После cd ls показывает новую папку."""
        self.ok("cd /etc")
        self.assertEqual(self.ok("ls"), "motd")

    def test_missing(self):
        """Нет такой папки: текущая папка не меняется."""
        self.ok("cd /etc")
        self.assertEqual(self.fail("cd /nope"),
                         "cd: /nope: No such file or directory")
        self.assertEqual(self.cwd(), "/etc")

    def test_file(self):
        """cd в файл."""
        self.assertEqual(self.fail("cd /readme.txt"),
                         "cd: /readme.txt: Not a directory")

    def test_too_many_args(self):
        """Больше одного аргумента."""
        self.assertEqual(self.fail("cd /etc /home"),
                         "cd: too many arguments")

    def test_option(self):
        """Опций у cd нет."""
        self.assertEqual(self.fail("cd -l"), "cd: invalid option -- 'l'")


class TacTest(CommandCase):
    """Команда tac."""

    def test_reverse_lines(self):
        """Строки идут в обратном порядке."""
        self.assertEqual(self.ok("tac /home/user/notes.txt"),
                         "третья строка\nвторая строка\nпервая строка")

    def test_relative_path(self):
        """Путь может быть относительным."""
        self.shell.execute("cd /home/user")
        self.assertTrue(self.ok("tac docs/todo.txt").startswith("3."))

    def test_several_files(self):
        """Несколько файлов: каждый переворачивается по очереди."""
        text = self.ok("tac /etc/motd /home/user/notes.txt")
        self.assertEqual(text.splitlines()[0], "Добро пожаловать в эмулятор!")
        self.assertEqual(text.splitlines()[1], "третья строка")

    def test_binary_file_does_not_crash(self):
        """Двоичный файл выводится с заменой неверных байт."""
        self.assertIn("BIN", self.ok("tac /home/user/photo.bin"))

    def test_no_operand(self):
        """Без аргументов."""
        self.assertEqual(self.fail("tac"), "tac: missing file operand")

    def test_missing_file(self):
        """Нет файла."""
        self.assertEqual(self.fail("tac /nope.txt"),
                         "tac: /nope.txt: No such file or directory")

    def test_directory(self):
        """Вместо файла папка."""
        self.assertEqual(self.fail("tac /etc"), "tac: /etc: Is a directory")

    def test_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.fail("tac -x /etc/motd"),
                         "tac: invalid option -- 'x'")


if __name__ == "__main__":
    unittest.main()
