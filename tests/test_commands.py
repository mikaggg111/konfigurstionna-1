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

    def error_of(self, line):
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
        self.assertEqual(self.ok("ls"), "config/  info.txt  projects/  users/  void/")

    def test_path(self):
        """ls с путём к папке."""
        self.assertEqual(self.ok("ls /users/student"),
                         "diary.txt  picture.bin  work/")

    def test_relative_path(self):
        """ls с относительным путём."""
        self.shell.execute("cd /users")
        self.assertEqual(self.ok("ls student/work"), "old/  tasks.txt")

    def test_file(self):
        """ls для файла печатает его имя как указано."""
        self.assertEqual(self.ok("ls /config/welcome.txt"), "/config/welcome.txt")

    def test_empty_dir(self):
        """У пустой папки нет вывода."""
        self.assertEqual(self.ok("ls /void"), "")

    def test_long(self):
        """ls -l: тип, размер и имя."""
        size = self.size_of("/config/welcome.txt")
        self.assertEqual(self.ok("ls -l /config"), f"- {size:>6} welcome.txt")
        self.assertEqual(self.ok("ls -l /void"), "")
        first = self.ok("ls -l").splitlines()[0]
        self.assertEqual(first, "d      0 config")

    def test_multiple_paths(self):
        """Несколько папок: заголовки и пустая строка между ними."""
        self.assertEqual(self.ok("ls /config /void"), "/config:\nwelcome.txt\n\n/void:")

    def test_missing(self):
        """Нет такого пути."""
        self.assertEqual(self.error_of("ls /nope"),
                         "ls: /nope: No such file or directory")

    def test_through_file(self):
        """Путь через файл."""
        self.assertIn("Not a directory", self.error_of("ls /info.txt/x"))

    def test_bad_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.error_of("ls -x"), "ls: invalid option -- 'x'")


class CdTest(CommandCase):
    """Команда cd."""

    def cwd(self):
        """Текущая папка VFS."""
        return self.shell.vfs.cwd_path()

    def test_absolute_and_relative(self):
        """Абсолютный и относительный переходы."""
        self.ok("cd /users/student/work")
        self.assertEqual(self.cwd(), "/users/student/work")
        self.ok("cd old/2024")
        self.assertEqual(self.cwd(), "/users/student/work/old/2024")

    def test_dots(self):
        """. и .. работают."""
        self.ok("cd /users/student/work/old")
        self.ok("cd ../..")
        self.assertEqual(self.cwd(), "/users/student")
        self.ok("cd .")
        self.assertEqual(self.cwd(), "/users/student")

    def test_above_root(self):
        """Выше корня подняться нельзя."""
        self.ok("cd /users")
        self.ok("cd ../../..")
        self.assertEqual(self.cwd(), "/")

    def test_no_args_goes_to_root(self):
        """cd без аргументов - в корень."""
        self.ok("cd /config")
        self.ok("cd")
        self.assertEqual(self.cwd(), "/")

    def test_ls_follows_cd(self):
        """После cd ls показывает новую папку."""
        self.ok("cd /config")
        self.assertEqual(self.ok("ls"), "welcome.txt")

    def test_missing(self):
        """Нет такой папки: текущая папка не меняется."""
        self.ok("cd /config")
        self.assertEqual(self.error_of("cd /nope"),
                         "cd: /nope: No such file or directory")
        self.assertEqual(self.cwd(), "/config")

    def test_file(self):
        """cd в файл."""
        self.assertEqual(self.error_of("cd /info.txt"),
                         "cd: /info.txt: Not a directory")

    def test_too_many_args(self):
        """Больше одного аргумента."""
        self.assertEqual(self.error_of("cd /config /users"),
                         "cd: too many arguments")

    def test_option(self):
        """Опций у cd нет."""
        self.assertEqual(self.error_of("cd -l"), "cd: invalid option -- 'l'")


class TacTest(CommandCase):
    """Команда tac."""

    def test_reverse_lines(self):
        """Строки идут в обратном порядке."""
        self.assertEqual(self.ok("tac /users/student/diary.txt"),
                         "вечер\nдень\nутро")

    def test_relative_path(self):
        """Путь может быть относительным."""
        self.shell.execute("cd /users/student")
        self.assertTrue(self.ok("tac work/tasks.txt").startswith("3."))

    def test_several_files(self):
        """Несколько файлов: каждый переворачивается по очереди."""
        text = self.ok("tac /config/welcome.txt /users/student/diary.txt")
        self.assertEqual(text.splitlines()[0], "Рады видеть вас в эмуляторе!")
        self.assertEqual(text.splitlines()[1], "вечер")

    def test_binary_file_does_not_crash(self):
        """Двоичный файл выводится с заменой неверных байт."""
        self.assertIn("BIN", self.ok("tac /users/student/picture.bin"))

    def test_no_operand(self):
        """Без аргументов."""
        self.assertEqual(self.error_of("tac"), "tac: missing file operand")

    def test_missing_file(self):
        """Нет файла."""
        self.assertEqual(self.error_of("tac /nope.txt"),
                         "tac: /nope.txt: No such file or directory")

    def test_directory(self):
        """Вместо файла папка."""
        self.assertEqual(self.error_of("tac /config"), "tac: /config: Is a directory")

    def test_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.error_of("tac -x /config/welcome.txt"),
                         "tac: invalid option -- 'x'")


if __name__ == "__main__":
    unittest.main()
