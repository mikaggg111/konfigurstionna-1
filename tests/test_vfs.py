"""Тесты виртуальной файловой системы и загрузки из CSV."""
import hashlib
import os
import tempfile
import unittest

import _path
from errors import ShellError
from vfs import Vfs, VfsNode, load_vfs

VFS_DIR = os.path.join(os.path.dirname(__file__), "..", "vfs")
HEADER = "path,type,content\n"
HELLO_B64 = "SGVsbG8="


def sample(name):
    """Возвращает путь к примеру VFS из папки vfs."""
    return os.path.join(VFS_DIR, name)


class LoadCase(unittest.TestCase):
    """Базовый класс: создаёт временные CSV-файлы."""

    def csv_file(self, text, encoding="utf-8"):
        """Записывает текст во временный CSV и возвращает путь."""
        handle, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(handle, "w", encoding=encoding, newline="") as file:
            file.write(text)
        self.addCleanup(os.remove, path)
        return path

    def load(self, rows):
        """Загружает VFS из строк CSV (заголовок добавляется сам)."""
        return load_vfs(self.csv_file(HEADER + rows))

    def assertBroken(self, rows, fragment):
        """Проверяет, что CSV не загружается, а в ошибке есть fragment."""
        with self.assertRaises(ShellError) as context:
            self.load(rows)
        self.assertIn(fragment, str(context.exception))


class LoadTest(LoadCase):
    """Загрузка корректных CSV."""

    def test_single_file(self):
        """Файл читается из base64 в байты."""
        vfs = self.load(f"/hello.txt,file,{HELLO_B64}\n")
        self.assertEqual(vfs.find("/hello.txt").content, b"Hello")
        self.assertEqual(vfs.count(), (0, 1))

    def test_nested_levels(self):
        """Вложенность задаётся полным путём; папки создаются сами."""
        vfs = self.load(f"/a/b/c/d.txt,file,{HELLO_B64}\n")
        self.assertTrue(vfs.find("/a/b/c").is_dir)
        self.assertEqual(vfs.find("/a/b/c/d.txt").content, b"Hello")
        self.assertEqual(vfs.count(), (3, 1))

    def test_empty_dir_row(self):
        """Строка типа dir создаёт пустую папку."""
        vfs = self.load("/empty,dir,\n")
        self.assertTrue(vfs.find("/empty").is_dir)
        self.assertEqual(vfs.find("/empty").children, {})

    def test_binary_data(self):
        """Двоичные данные сохраняются через base64 без потерь."""
        vfs = load_vfs(sample("deep.csv"))
        data = vfs.find("/home/user/photo.bin").content
        self.assertEqual(data, b"\x89BIN\r\n\x00\x01\x02\xff")

    def test_name_is_file_name(self):
        """Имя VFS - имя CSV-файла без папок."""
        self.assertEqual(load_vfs(sample("minimal.csv")).name, "minimal.csv")

    def test_bom_crlf_and_spaces(self):
        """BOM, переводы строк CRLF и пробелы в заголовке допустимы."""
        text = "﻿path , Type,content\r\n/a.txt,FILE," + HELLO_B64 + "\r\n"
        vfs = load_vfs(self.csv_file(text, "utf-8"))
        self.assertEqual(vfs.find("/a.txt").content, b"Hello")

    def test_samples_load(self):
        """Все примеры из папки vfs загружаются."""
        self.assertEqual(load_vfs(sample("minimal.csv")).count(), (0, 1))
        self.assertEqual(load_vfs(sample("several.csv")).count(), (1, 4))
        self.assertEqual(load_vfs(sample("deep.csv")).count(), (7, 6))

    def test_deep_sample_has_three_levels(self):
        """В deep.csv есть путь глубиной не менее трёх уровней."""
        vfs = load_vfs(sample("deep.csv"))
        node = vfs.find("/home/user/docs/archive/2025/report.txt")
        self.assertFalse(node.is_dir)

    def test_disk_file_is_not_modified(self):
        """Загрузка не меняет файл на диске."""
        path = sample("deep.csv")
        with open(path, "rb") as file:
            before = hashlib.sha256(file.read()).hexdigest()
        load_vfs(path)
        with open(path, "rb") as file:
            after = hashlib.sha256(file.read()).hexdigest()
        self.assertEqual(before, after)


class LoadErrorTest(LoadCase):
    """Ошибки загрузки."""

    def test_file_not_found(self):
        """Нет файла."""
        with self.assertRaises(ShellError) as context:
            load_vfs("no_such_vfs.csv")
        self.assertIn("не найдена", str(context.exception))

    def test_path_is_directory(self):
        """Вместо файла указана папка."""
        with self.assertRaises(ShellError) as context:
            load_vfs(VFS_DIR)
        self.assertIn("папка", str(context.exception))

    def test_empty_file(self):
        """Пустой файл без заголовка."""
        with self.assertRaises(ShellError):
            load_vfs(self.csv_file(""))

    def test_missing_columns(self):
        """В заголовке нет нужных столбцов."""
        with self.assertRaises(ShellError) as context:
            load_vfs(self.csv_file("name,kind\n/a,file\n"))
        self.assertIn("нет столбцов", str(context.exception))

    def test_broken_samples(self):
        """Примеры плохих CSV из vfs/broken не загружаются."""
        for name in ("bad_columns", "bad_type", "bad_base64"):
            with self.subTest(name=name):
                with self.assertRaises(ShellError):
                    load_vfs(sample(f"broken/{name}.csv"))

    def test_unknown_type_has_line_number(self):
        """Ошибка в строке данных сообщает её номер."""
        self.assertBroken("/a,dir,\n/b,folder,\n", "строка 3")

    def test_bad_base64(self):
        """Содержимое не в base64."""
        self.assertBroken("/a.txt,file,!!!\n", "base64")

    def test_relative_path(self):
        """Путь без ведущего /."""
        self.assertBroken("a.txt,file,\n", "должен начинаться")

    def test_dots_in_path(self):
        """Точки в пути запрещены."""
        self.assertBroken("/a/../b.txt,file,\n", "'.' и '..'")

    def test_duplicate_file(self):
        """Один путь дважды."""
        self.assertBroken("/a.txt,file,\n/a.txt,file,\n", "уже есть")

    def test_file_used_as_folder(self):
        """Файл не может быть папкой для другого элемента."""
        self.assertBroken("/a,file,\n/a/b,file,\n", "файл, а не папка")

    def test_root_as_file(self):
        """У файла должно быть имя."""
        self.assertBroken("/,file,\n", "должно быть имя")

    def test_short_row(self):
        """В строке не хватает полей: тип не задан."""
        self.assertBroken("/a.txt\n", "неизвестный тип")


class PathTest(unittest.TestCase):
    """Пути и поиск узлов."""

    def setUp(self):
        """Готовит VFS с папкой /a/b и файлом /a/f."""
        self.vfs = Vfs()
        self.vfs.make_dirs(["a", "b"])
        self.vfs.find("/a").children["f"] = VfsNode("f", False, b"x")

    def test_split_path(self):
        """Абсолютные и относительные пути, . и .. ."""
        self.vfs.cwd = ["a"]
        self.assertEqual(self.vfs.split_path("/a/b"), ["a", "b"])
        self.assertEqual(self.vfs.split_path("b"), ["a", "b"])
        self.assertEqual(self.vfs.split_path("./b/.."), ["a"])
        self.assertEqual(self.vfs.split_path("../.."), [])

    def test_cwd_path(self):
        """Путь текущей папки."""
        self.assertEqual(self.vfs.cwd_path(), "/")
        self.vfs.cwd = ["a", "b"]
        self.assertEqual(self.vfs.cwd_path(), "/a/b")

    def test_find_missing(self):
        """Нет такого пути."""
        with self.assertRaises(ShellError) as context:
            self.vfs.find("/a/zzz")
        self.assertIn("No such file or directory", str(context.exception))

    def test_find_through_file(self):
        """Внутрь файла зайти нельзя."""
        with self.assertRaises(ShellError) as context:
            self.vfs.find("/a/f/x")
        self.assertIn("Not a directory", str(context.exception))

    def test_lookup(self):
        """lookup возвращает родителя, имя и узел (или None)."""
        parent, name, node = self.vfs.lookup("/a/new")
        self.assertIs(parent, self.vfs.find("/a"))
        self.assertEqual((name, node), ("new", None))
        _, _, root = self.vfs.lookup("/")
        self.assertIs(root, self.vfs.root)

    def test_clone_is_deep(self):
        """Копия узла не зависит от оригинала."""
        original = self.vfs.find("/a")
        copy = original.clone("copy")
        copy.children["f"].content = b"changed"
        self.assertEqual(original.children["f"].content, b"x")
        self.assertEqual(copy.name, "copy")


if __name__ == "__main__":
    unittest.main()
