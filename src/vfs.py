"""Виртуальная файловая система (VFS), которая целиком хранится в памяти.

Источник VFS - CSV-файл со столбцами path, type, content:

* path    - полный путь от корня, например /home/user/notes.txt;
* type    - dir (папка) или file (файл);
* content - содержимое файла в base64 (у папки пусто).

Вложенность задаётся полным путём: родитель - всё до последнего "/".
Недостающие промежуточные папки создаются сами. После загрузки с диском
больше никаких операций нет: файл CSV никогда не изменяется.
"""
import base64
import csv
import os
from typing import Dict, List, Optional, Tuple

from errors import ShellError

SEPARATOR = "/"
ROOT_NAME = "/"
CURRENT_DIR = "."
PARENT_DIR = ".."
DEFAULT_NAME = "default"
DIR_TYPE = "dir"
FILE_TYPE = "file"
CSV_COLUMNS = ("path", "type", "content")
CSV_ENCODING = "utf-8-sig"


class VfsNode:
    """Файл или папка VFS. У папки есть children, у файла - content."""

    def __init__(self, name: str, is_dir: bool, content: bytes = b""):
        """Создаёт узел: имя, признак папки и байты содержимого."""
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.children: Dict[str, "VfsNode"] = {}

    def clone(self, name: Optional[str] = None) -> "VfsNode":
        """Возвращает глубокую копию узла, при желании с новым именем."""
        copy = VfsNode(name or self.name, self.is_dir, self.content)
        for child_name, child in self.children.items():
            copy.children[child_name] = child.clone()
        return copy


Lookup = Tuple[Optional[VfsNode], str, Optional[VfsNode]]


class Vfs:
    """VFS целиком: корневая папка, имя и текущая папка (cwd)."""

    def __init__(self, root: Optional[VfsNode] = None,
                 name: str = DEFAULT_NAME):
        """Создаёт VFS. Без root получается пустая VFS."""
        self.root = root or VfsNode(ROOT_NAME, True)
        self.name = name
        self.cwd: List[str] = []

    def cwd_path(self) -> str:
        """Возвращает путь текущей папки, например /home/user."""
        return SEPARATOR + SEPARATOR.join(self.cwd)

    def split_path(self, path: str) -> List[str]:
        """Превращает путь в список имён от корня.

        Понимает абсолютные и относительные пути, "." и "..".
        """
        parts = [] if path.startswith(SEPARATOR) else list(self.cwd)
        for part in path.split(SEPARATOR):
            if part in ("", CURRENT_DIR):
                continue
            if part == PARENT_DIR:
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return parts

    @staticmethod
    def walk(parts: List[str], root: VfsNode, path: str) -> VfsNode:
        """Идёт от root по именам parts; ошибка, если пути нет."""
        node = root
        for part in parts:
            if not node.is_dir:
                raise ShellError(f"{path}: Not a directory")
            child = node.children.get(part)
            if child is None:
                raise ShellError(f"{path}: No such file or directory")
            node = child
        return node

    def find(self, path: str) -> VfsNode:
        """Находит узел по пути или выбрасывает ShellError."""
        return self.walk(self.split_path(path), self.root, path)

    def lookup(self, path: str) -> Lookup:
        """Ищет узел по пути и возвращает (родитель, имя, узел или None).

        Нужен командам, которые создают новые узлы (cp). Для корня
        родителя нет.
        """
        parts = self.split_path(path)
        if not parts:
            return None, self.root.name, self.root
        parent = self.walk(parts[:-1], self.root, path)
        if not parent.is_dir:
            raise ShellError(f"{path}: Not a directory")
        return parent, parts[-1], parent.children.get(parts[-1])

    def make_dirs(self, parts: List[str]) -> VfsNode:
        """Создаёт недостающие папки по списку имён, возвращает последнюю."""
        node = self.root
        for part in parts:
            child = node.children.get(part)
            if child is None:
                child = VfsNode(part, True)
                node.children[part] = child
            elif not child.is_dir:
                raise ShellError(f"'{part}' - файл, а не папка")
            node = child
        return node

    def count(self) -> Tuple[int, int]:
        """Возвращает (число папок, число файлов) без учёта корня."""
        dirs = files = 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            for child in node.children.values():
                if child.is_dir:
                    dirs += 1
                    stack.append(child)
                else:
                    files += 1
        return dirs, files


def decode_base64(text: str) -> bytes:
    """Переводит содержимое из base64 в байты (пробелы игнорируются)."""
    try:
        return base64.b64decode("".join(text.split()), validate=True)
    except ValueError as error:
        raise ShellError("содержимое не в формате base64") from error


def parse_path(path: str) -> List[str]:
    """Проверяет путь из CSV и возвращает список имён от корня."""
    if not path.startswith(SEPARATOR):
        raise ShellError(f"путь '{path}' должен начинаться с '/'")
    parts = [part for part in path.split(SEPARATOR) if part]
    if CURRENT_DIR in parts or PARENT_DIR in parts:
        raise ShellError(f"в пути '{path}' не должно быть '.' и '..'")
    return parts


def add_file(vfs: Vfs, parts: List[str], text: str):
    """Добавляет файл с содержимым из base64 по списку имён."""
    if not parts:
        raise ShellError("у файла должно быть имя, а не '/'")
    data = decode_base64(text)
    parent = vfs.make_dirs(parts[:-1])
    name = parts[-1]
    if name in parent.children:
        raise ShellError(f"'{SEPARATOR.join(parts)}' уже есть в VFS")
    parent.children[name] = VfsNode(name, False, data)


def add_row(vfs: Vfs, row: Dict[str, Optional[str]]):
    """Добавляет в VFS одну строку CSV (папку или файл)."""
    path = (row.get("path") or "").strip()
    kind = (row.get("type") or "").strip().lower()
    parts = parse_path(path)
    if kind == DIR_TYPE:
        vfs.make_dirs(parts)
    elif kind == FILE_TYPE:
        add_file(vfs, parts, row.get("content") or "")
    else:
        raise ShellError(f"неизвестный тип '{kind}', нужен dir или file")


def read_csv(reader: csv.DictReader) -> Vfs:
    """Строит VFS из строк CSV; ошибка содержит номер строки."""
    names = reader.fieldnames
    if not names:
        raise ShellError("неверный формат VFS: файл пустой")
    reader.fieldnames = [name.strip().lower() for name in names]
    missing = [name for name in CSV_COLUMNS if name not in reader.fieldnames]
    if missing:
        raise ShellError(
            f"неверный формат VFS: нет столбцов {', '.join(missing)}"
        )
    vfs = Vfs()
    for row in reader:
        try:
            add_row(vfs, row)
        except ShellError as error:
            raise ShellError(
                f"неверный формат VFS, строка {reader.line_num}: {error}"
            ) from error
    return vfs


def load_vfs(path: str) -> Vfs:
    """Загружает VFS из CSV-файла целиком в память.

    Ошибки: файл не найден, путь указывает на папку, нет нужных
    столбцов, неверный тип, неверный base64, неверный путь.
    """
    if not os.path.exists(path):
        raise ShellError(f"VFS не найдена: '{path}'")
    if os.path.isdir(path):
        raise ShellError(
            f"неверный формат VFS: '{path}' - папка, а нужен CSV-файл"
        )
    try:
        with open(path, newline="", encoding=CSV_ENCODING) as file:
            vfs = read_csv(csv.DictReader(file))
    except OSError as error:
        raise ShellError(f"ошибка чтения VFS: {error.strerror}") from error
    except UnicodeDecodeError as error:
        raise ShellError("неверный формат VFS: не UTF-8") from error
    except csv.Error as error:
        raise ShellError(f"неверный формат VFS: {error}") from error
    vfs.name = os.path.basename(path)
    return vfs
