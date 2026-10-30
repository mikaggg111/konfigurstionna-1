"""Тесты команды cp на примере vfs/deep.csv."""
import hashlib
import os
import unittest

from shell import Shell
from vfs import load_vfs

DEEP = os.path.join(os.path.dirname(__file__), "..", "vfs", "deep.csv")
MOTD = "Добро пожаловать в эмулятор!\n".encode("utf-8")


class CpCase(unittest.TestCase):
    """Базовый класс: Shell с VFS deep.csv."""

    def setUp(self):
        """Загружает VFS и создаёт Shell."""
        self.shell = Shell(load_vfs(DEEP))
        self.vfs = self.shell.vfs

    def ok(self, line):
        """Выполняет команду и проверяет, что ошибки нет."""
        result = self.shell.execute(line)
        self.assertEqual(result.error, "")
        return result.output

    def fail(self, line):
        """Выполняет команду и возвращает текст её ошибки."""
        result = self.shell.execute(line)
        self.assertNotEqual(result.error, "", f"'{line}' не дала ошибки")
        return result.error

    def content(self, path):
        """Содержимое файла VFS."""
        return self.vfs.find(path).content


class CpFilesTest(CpCase):
    """Копирование файлов."""

    def test_file_to_new_name(self):
        """Файл в новое имя; оригинал остаётся."""
        self.ok("cp /etc/motd /home/user/motd.copy")
        self.assertEqual(self.content("/home/user/motd.copy"), MOTD)
        self.assertEqual(self.content("/etc/motd"), MOTD)

    def test_file_into_directory(self):
        """Файл в существующую папку - имя сохраняется."""
        self.ok("cp /etc/motd /empty")
        self.assertEqual(self.ok("ls /empty"), "motd")

    def test_overwrite_file(self):
        """Существующий файл заменяется."""
        self.ok("cp /etc/motd /readme.txt")
        self.assertEqual(self.content("/readme.txt"), MOTD)

    def test_several_files_into_directory(self):
        """Несколько файлов в папку."""
        self.ok("cp /etc/motd /readme.txt /empty")
        self.assertEqual(self.ok("ls /empty"), "motd  readme.txt")

    def test_relative_paths(self):
        """Относительные пути считаются от текущей папки."""
        self.ok("cd /home/user")
        self.ok("cp notes.txt docs")
        self.assertEqual(self.content("/home/user/docs/notes.txt"),
                         self.content("/home/user/notes.txt"))

    def test_binary_file(self):
        """Двоичный файл копируется без потерь."""
        self.ok("cp /home/user/photo.bin /empty/copy.bin")
        self.assertEqual(self.content("/empty/copy.bin"),
                         self.content("/home/user/photo.bin"))

    def test_copy_is_independent(self):
        """Копия - отдельный узел, а не ссылка на оригинал."""
        self.ok("cp /etc/motd /empty/motd")
        self.assertIsNot(self.vfs.find("/empty/motd"),
                         self.vfs.find("/etc/motd"))

    def test_source_and_dest_can_be_dots(self):
        """В пути можно использовать . и .. ."""
        self.ok("cd /etc")
        self.ok("cp motd ../empty/m2")
        self.assertEqual(self.content("/empty/m2"), MOTD)


class CpDirectoriesTest(CpCase):
    """Копирование папок (cp -r)."""

    def test_directory_to_new_name(self):
        """Папка целиком в новое имя."""
        before = self.vfs.count()
        self.ok("cp -r /home/user/docs /backup")
        self.assertEqual(
            self.content("/backup/archive/2025/report.txt"),
            self.content("/home/user/docs/archive/2025/report.txt"))
        self.assertEqual(self.vfs.count(), (before[0] + 4, before[1] + 2))

    def test_directory_into_existing_directory(self):
        """Папка в существующую папку - кладётся внутрь."""
        self.ok("cp -r /home/user/docs /empty")
        self.assertEqual(self.ok("ls /empty"), "docs/")
        self.assertTrue(self.vfs.find("/empty/docs/todo.txt"))

    def test_merge_keeps_existing_files(self):
        """Повторное копирование сливает папки, лишние файлы остаются."""
        self.ok("cp -r /home/user/docs /empty")
        self.ok("cp /etc/motd /empty/docs/extra.txt")
        self.ok("cp -r /home/user/docs /empty")
        self.assertEqual(self.ok("ls /empty/docs"),
                         "archive/  extra.txt  todo.txt")

    def test_copy_does_not_change_original(self):
        """Правка копии не влияет на оригинал."""
        self.ok("cp -r /home/user/docs /backup")
        self.ok("cp /etc/motd /backup/todo.txt")
        self.assertNotEqual(self.content("/home/user/docs/todo.txt"), MOTD)

    def test_combined_option_syntax(self):
        """Опции можно писать слитно, например -r."""
        self.ok("cp -r /etc /etc2")
        self.assertEqual(self.ok("ls /etc2"), "motd")


class CpMemoryOnlyTest(CpCase):
    """cp меняет только память."""

    def test_csv_file_is_not_modified(self):
        """После cp файл CSV на диске точно такой же."""
        with open(DEEP, "rb") as file:
            before = hashlib.sha256(file.read()).hexdigest()
        self.ok("cp -r /home /backup")
        self.ok("cp /etc/motd /readme.txt")
        with open(DEEP, "rb") as file:
            after = hashlib.sha256(file.read()).hexdigest()
        self.assertEqual(before, after)

    def test_new_shell_starts_from_original(self):
        """Новый запуск загружает исходную VFS без копий."""
        self.ok("cp -r /home /backup")
        fresh = Shell(load_vfs(DEEP))
        self.assertEqual(fresh.execute("ls").output,
                         "empty/  etc/  home/  readme.txt")


class CpErrorsTest(CpCase):
    """Ошибки cp."""

    def test_no_operands(self):
        """Нет аргументов."""
        self.assertEqual(self.fail("cp"), "cp: missing file operand")

    def test_no_destination(self):
        """Нет назначения."""
        self.assertEqual(
            self.fail("cp /etc/motd"),
            "cp: missing destination file operand after '/etc/motd'")

    def test_missing_source(self):
        """Нет источника."""
        self.assertEqual(self.fail("cp /nope /empty"),
                         "cp: /nope: No such file or directory")

    def test_missing_destination_folder(self):
        """Нет папки для нового файла."""
        self.assertEqual(self.fail("cp /etc/motd /no/such/file"),
                         "cp: /no/such/file: No such file or directory")

    def test_directory_without_r(self):
        """Папка без -r."""
        self.assertEqual(
            self.fail("cp /etc /empty"),
            "cp: -r not specified; omitting directory '/etc'")

    def test_target_is_not_directory(self):
        """Несколько источников, а назначение не папка."""
        self.assertEqual(
            self.fail("cp /etc/motd /readme.txt /home/user/notes.txt"),
            "cp: target '/home/user/notes.txt' is not a directory")

    def test_copy_into_itself(self):
        """Папку нельзя скопировать в саму себя."""
        self.assertEqual(
            self.fail("cp -r /home /home/user/x"),
            "cp: cannot copy a directory, '/home', into itself, "
            "'/home/user/x'")

    def test_same_file(self):
        """Файл в самого себя."""
        self.assertEqual(self.fail("cp /etc/motd /etc/motd"),
                         "cp: '/etc/motd' and '/etc/motd' are the same file")
        self.assertIn("same file", self.fail("cp /etc/motd /etc"))

    def test_directory_over_file(self):
        """Папкой нельзя заменить файл."""
        self.assertEqual(
            self.fail("cp -r /etc /readme.txt"),
            "cp: cannot overwrite non-directory 'readme.txt' "
            "with directory")

    def test_file_over_directory(self):
        """Файлом нельзя заменить папку."""
        self.vfs.make_dirs(["empty", "motd"])
        self.assertEqual(
            self.fail("cp /etc/motd /empty"),
            "cp: cannot overwrite directory 'motd' with non-directory")

    def test_root(self):
        """Корень копировать нельзя."""
        self.assertEqual(self.fail("cp -r / /empty"),
                         "cp: cannot copy the root directory")

    def test_bad_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.fail("cp -x /etc/motd /empty"),
                         "cp: invalid option -- 'x'")

    def test_nothing_changes_after_error(self):
        """После ошибки VFS не меняется."""
        before = self.vfs.count()
        self.fail("cp -r /home /home/user/x")
        self.assertEqual(self.vfs.count(), before)


if __name__ == "__main__":
    unittest.main()
