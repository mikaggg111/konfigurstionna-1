"""Тесты команды cp на примере vfs/deep.csv."""
import hashlib
import os
import unittest

from shell import Shell
from vfs import load_vfs

DEEP = os.path.join(os.path.dirname(__file__), "..", "vfs", "deep.csv")
MOTD = "Рады видеть вас в эмуляторе!\n".encode("utf-8")


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

    def error_of(self, line):
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
        self.ok("cp /config/welcome.txt /users/student/welcome.copy")
        self.assertEqual(self.content("/users/student/welcome.copy"), MOTD)
        self.assertEqual(self.content("/config/welcome.txt"), MOTD)

    def test_file_into_directory(self):
        """Файл в существующую папку - имя сохраняется."""
        self.ok("cp /config/welcome.txt /void")
        self.assertEqual(self.ok("ls /void"), "welcome.txt")

    def test_overwrite_file(self):
        """Существующий файл заменяется."""
        self.ok("cp /config/welcome.txt /info.txt")
        self.assertEqual(self.content("/info.txt"), MOTD)

    def test_several_files_into_directory(self):
        """Несколько файлов в папку."""
        self.ok("cp /config/welcome.txt /info.txt /void")
        self.assertEqual(self.ok("ls /void"), "info.txt  welcome.txt")

    def test_relative_paths(self):
        """Относительные пути считаются от текущей папки."""
        self.ok("cd /users/student")
        self.ok("cp diary.txt work")
        self.assertEqual(self.content("/users/student/work/diary.txt"),
                         self.content("/users/student/diary.txt"))

    def test_binary_file(self):
        """Двоичный файл копируется без потерь."""
        self.ok("cp /users/student/picture.bin /void/copy.bin")
        self.assertEqual(self.content("/void/copy.bin"),
                         self.content("/users/student/picture.bin"))

    def test_copy_is_independent(self):
        """Копия - отдельный узел, а не ссылка на оригинал."""
        self.ok("cp /config/welcome.txt /void/welcome.txt")
        self.assertIsNot(self.vfs.find("/void/welcome.txt"),
                         self.vfs.find("/config/welcome.txt"))

    def test_source_and_dest_can_be_dots(self):
        """В пути можно использовать . и .. ."""
        self.ok("cd /config")
        self.ok("cp welcome.txt ../void/m2")
        self.assertEqual(self.content("/void/m2"), MOTD)


class CpDirectoriesTest(CpCase):
    """Копирование папок (cp -r)."""

    def test_directory_to_new_name(self):
        """Папка целиком в новое имя."""
        before = self.vfs.count()
        self.ok("cp -r /users/student/work /backup")
        self.assertEqual(
            self.content("/backup/old/2024/summary.txt"),
            self.content("/users/student/work/old/2024/summary.txt"))
        self.assertEqual(self.vfs.count(), (before[0] + 3, before[1] + 2))

    def test_directory_into_existing_directory(self):
        """Папка в существующую папку - кладётся внутрь."""
        self.ok("cp -r /users/student/work /void")
        self.assertEqual(self.ok("ls /void"), "work/")
        self.assertTrue(self.vfs.find("/void/work/tasks.txt"))

    def test_merge_keeps_existing_files(self):
        """Повторное копирование сливает папки, лишние файлы остаются."""
        self.ok("cp -r /users/student/work /void")
        self.ok("cp /config/welcome.txt /void/work/extra.txt")
        self.ok("cp -r /users/student/work /void")
        self.assertEqual(self.ok("ls /void/work"),
                         "extra.txt  old/  tasks.txt")

    def test_copy_does_not_change_original(self):
        """Правка копии не влияет на оригинал."""
        self.ok("cp -r /users/student/work /backup")
        self.ok("cp /config/welcome.txt /backup/tasks.txt")
        self.assertNotEqual(self.content("/users/student/work/tasks.txt"), MOTD)

    def test_combined_option_syntax(self):
        """Опции можно писать слитно, например -r."""
        self.ok("cp -r /config /config2")
        self.assertEqual(self.ok("ls /config2"), "welcome.txt")


class CpMemoryOnlyTest(CpCase):
    """cp меняет только память."""

    def test_csv_file_is_not_modified(self):
        """После cp файл CSV на диске точно такой же."""
        with open(DEEP, "rb") as file:
            before = hashlib.sha256(file.read()).hexdigest()
        self.ok("cp -r /users /backup")
        self.ok("cp /config/welcome.txt /info.txt")
        with open(DEEP, "rb") as file:
            after = hashlib.sha256(file.read()).hexdigest()
        self.assertEqual(before, after)

    def test_new_shell_starts_from_original(self):
        """Новый запуск загружает исходную VFS без копий."""
        self.ok("cp -r /users /backup")
        fresh = Shell(load_vfs(DEEP))
        self.assertEqual(fresh.execute("ls").output,
                         "config/  info.txt  projects/  users/  void/")


class CpErrorsTest(CpCase):
    """Ошибки cp."""

    def test_no_operands(self):
        """Нет аргументов."""
        self.assertEqual(self.error_of("cp"), "cp: missing file operand")

    def test_no_destination(self):
        """Нет назначения."""
        self.assertEqual(
            self.error_of("cp /config/welcome.txt"),
            "cp: missing destination file operand after '/config/welcome.txt'")

    def test_missing_source(self):
        """Нет источника."""
        self.assertEqual(self.error_of("cp /nope /void"),
                         "cp: /nope: No such file or directory")

    def test_missing_destination_folder(self):
        """Нет папки для нового файла."""
        self.assertEqual(self.error_of("cp /config/welcome.txt /no/such/file"),
                         "cp: /no/such/file: No such file or directory")

    def test_directory_without_r(self):
        """Папка без -r."""
        self.assertEqual(
            self.error_of("cp /config /void"),
            "cp: -r not specified; omitting directory '/config'")

    def test_target_is_not_directory(self):
        """Несколько источников, а назначение не папка."""
        self.assertEqual(
            self.error_of(
                "cp /config/welcome.txt /info.txt /users/student/diary.txt"),
            "cp: target '/users/student/diary.txt' is not a directory")

    def test_copy_into_itself(self):
        """Папку нельзя скопировать в саму себя."""
        self.assertEqual(
            self.error_of("cp -r /users /users/student/x"),
            "cp: cannot copy a directory, '/users', into itself, "
            "'/users/student/x'")

    def test_same_file(self):
        """Файл в самого себя."""
        text = "cp /config/welcome.txt /config/welcome.txt"
        self.assertEqual(
            self.error_of(text),
            "cp: '/config/welcome.txt' and '/config/welcome.txt' "
            "are the same file")
        error = self.error_of("cp /config/welcome.txt /config")
        self.assertIn("same file", error)

    def test_directory_over_file(self):
        """Папкой нельзя заменить файл."""
        self.assertEqual(
            self.error_of("cp -r /config /info.txt"),
            "cp: cannot overwrite non-directory 'info.txt' "
            "with directory")

    def test_file_over_directory(self):
        """Файлом нельзя заменить папку."""
        self.vfs.make_dirs(["void", "welcome.txt"])
        self.assertEqual(
            self.error_of("cp /config/welcome.txt /void"),
            "cp: cannot overwrite directory 'welcome.txt' with non-directory")

    def test_root(self):
        """Корень копировать нельзя."""
        self.assertEqual(self.error_of("cp -r / /void"),
                         "cp: cannot copy the root directory")

    def test_bad_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.error_of("cp -x /config/welcome.txt /void"),
                         "cp: invalid option -- 'x'")

    def test_nothing_changes_after_error(self):
        """После ошибки VFS не меняется."""
        before = self.vfs.count()
        self.error_of("cp -r /users /users/student/x")
        self.assertEqual(self.vfs.count(), before)


if __name__ == "__main__":
    unittest.main()
