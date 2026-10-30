"""Команды эмулятора, которые работают с VFS: ls, cd, tac.

Каждая команда - функция cmd_имя(vfs, args). Она возвращает текст вывода
или выбрасывает ShellError. Приставку "имя команды:" к ошибке добавляет
Shell.
"""
from typing import List

from errors import ShellError
from options import split_options
from vfs import CURRENT_DIR, ROOT_NAME, Vfs, VfsNode

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
