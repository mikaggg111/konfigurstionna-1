"""Команды эмулятора, которые работают с VFS: ls, cd, tac, cp.

Каждая команда - функция cmd_имя(vfs, args). Она возвращает текст вывода
или выбрасывает ShellError. Приставку "имя команды:" к ошибке добавляет
Shell.
"""
from typing import List, Optional

from errors import ShellError
from options import split_options
from vfs import CURRENT_DIR, ROOT_NAME, Lookup, Vfs, VfsNode

LS_OPTIONS = "l"
LONG_FLAG = "l"
DIR_SUFFIX = "/"
DIR_MARK = "d"
FILE_MARK = "-"
SIZE_WIDTH = 6
SHORT_SEPARATOR = "  "
LINE_BREAK = "\n"
ONE_ITEM = 1
MAX_CD_ARGS = 1
TEXT_ENCODING = "utf-8"


def label_of(name: str, node: VfsNode, long_format: bool) -> str:
    """Формирует одну запись списка ls: имя или строка для ls -l."""
    if long_format:
        mark = DIR_MARK if node.is_dir else FILE_MARK
        size = 0 if node.is_dir else len(node.content)
        return f"{mark} {size:>{SIZE_WIDTH}} {name}"
    return name + DIR_SUFFIX if node.is_dir else name


def format_node(node: VfsNode, path: str, long_format: bool) -> str:
    """Возвращает список ls для одного пути (папка или файл)."""
    if node.is_dir:
        items = sorted(node.children.items())
    else:
        items = [(path, node)]
    labels = [label_of(name, item, long_format) for name, item in items]
    return (LINE_BREAK if long_format else SHORT_SEPARATOR).join(labels)


def cmd_ls(vfs: Vfs, args: List[str]) -> str:
    """ls [-l] [путь...] - показать содержимое папок и файлов."""
    flags, paths = split_options(args, LS_OPTIONS)
    targets = paths or [CURRENT_DIR]
    blocks = []
    for path in targets:
        node = vfs.find(path)
        text = format_node(node, path, LONG_FLAG in flags)
        if len(targets) > ONE_ITEM and node.is_dir:
            text = f"{path}:" + (LINE_BREAK + text if text else "")
            text = (LINE_BREAK + text) if blocks else text
        blocks.append(text)
    return LINE_BREAK.join(blocks)


def cmd_cd(vfs: Vfs, args: List[str]) -> str:
    """cd [путь] - сменить текущую папку; без аргумента - в корень."""
    _, operands = split_options(args, "")
    if len(operands) > MAX_CD_ARGS:
        raise ShellError("too many arguments")
    path = operands[0] if operands else ROOT_NAME
    if not vfs.find(path).is_dir:
        raise ShellError(f"{path}: Not a directory")
    vfs.cwd = vfs.split_path(path)
    return ""


def reverse_lines(content: bytes) -> str:
    """Возвращает текст файла, в котором строки идут в обратном порядке."""
    text = content.decode(TEXT_ENCODING, errors="replace")
    return LINE_BREAK.join(reversed(text.splitlines()))


def cmd_tac(vfs: Vfs, args: List[str]) -> str:
    """tac файл... - вывести строки файлов в обратном порядке."""
    _, files = split_options(args, "")
    if not files:
        raise ShellError("missing file operand")
    parts = []
    for path in files:
        node = vfs.find(path)
        if node.is_dir:
            raise ShellError(f"{path}: Is a directory")
        parts.append(reverse_lines(node.content))
    return LINE_BREAK.join(parts)


CP_OPTIONS = "r"
RECURSIVE_FLAG = "r"
MIN_CP_OPERANDS = 2


def contains(ancestor: VfsNode, node: VfsNode) -> bool:
    """Проверяет, лежит ли node внутри ancestor (или это он сам)."""
    stack = [ancestor]
    while stack:
        current = stack.pop()
        if current is node:
            return True
        stack.extend(current.children.values())
    return False


def check_overwrite(existing: Optional[VfsNode], source: VfsNode, name: str):
    """Нельзя заменять папку файлом и файл папкой."""
    if existing is None:
        return
    if existing.is_dir and not source.is_dir:
        raise ShellError(f"cannot overwrite directory '{name}' "
                         "with non-directory")
    if source.is_dir and not existing.is_dir:
        raise ShellError(f"cannot overwrite non-directory '{name}' "
                         "with directory")


def place(parent: VfsNode, name: str, source: VfsNode):
    """Кладёт копию source в папку parent под именем name (только память).

    Файл заменяет файл. Папка, которая уже есть, не заменяется: в неё
    переносится содержимое (слияние), как делает cp -r.
    """
    existing = parent.children.get(name)
    check_overwrite(existing, source, name)
    if existing is not None and existing.is_dir:
        for child_name, child in source.children.items():
            place(existing, child_name, child)
        return
    parent.children[name] = source.clone(name)


def copy_one(vfs: Vfs, source_path: str, dest_path: str, dest: Lookup,
             recursive: bool):
    """Копирует один источник; dest - результат vfs.lookup(dest_path)."""
    source = vfs.find(source_path)
    if source is vfs.root:
        raise ShellError("cannot copy the root directory")
    if source.is_dir and not recursive:
        raise ShellError(
            f"-r not specified; omitting directory '{source_path}'")
    parent, name, node = dest
    if node is not None and node.is_dir:
        parent, name = node, source.name
    if parent.children.get(name) is source:
        raise ShellError(
            f"'{source_path}' and '{dest_path}' are the same file")
    if source.is_dir and contains(source, parent):
        raise ShellError(f"cannot copy a directory, '{source_path}', "
                         f"into itself, '{dest_path}'")
    place(parent, name, source)


def cmd_cp(vfs: Vfs, args: List[str]) -> str:
    """cp [-r] источник... назначение - копирование внутри VFS.

    Изменяется только VFS в памяти, CSV-файл на диске не трогается.
    """
    flags, operands = split_options(args, CP_OPTIONS)
    if not operands:
        raise ShellError("missing file operand")
    if len(operands) < MIN_CP_OPERANDS:
        raise ShellError(
            f"missing destination file operand after '{operands[0]}'")
    *sources, dest_path = operands
    dest = vfs.lookup(dest_path)
    dest_is_dir = dest[2] is not None and dest[2].is_dir
    if len(sources) > ONE_ITEM and not dest_is_dir:
        raise ShellError(f"target '{dest_path}' is not a directory")
    for source_path in sources:
        copy_one(vfs, source_path, dest_path, dest, RECURSIVE_FLAG in flags)
    return ""
