"""Точка входа эмулятора командной строки."""
from typing import List, Tuple

from config import Config, parse_args
from errors import ShellError
from gui import Note, run
from shell import Shell
from vfs import Vfs, load_vfs


def load_vfs_notes(config: Config) -> Tuple[Vfs, List[Note]]:
    """Загружает VFS по параметру --vfs и готовит сообщения о загрузке.

    При ошибке возвращается пустая VFS и сообщение об ошибке.
    """
    if not config.vfs_path:
        return Vfs(), [("VFS не задана, используется пустая VFS", "debug")]
    try:
        vfs = load_vfs(config.vfs_path)
    except ShellError as error:
        return Vfs(), [
            (f"Ошибка загрузки VFS: {error}", "error"),
            ("Используется пустая VFS", "debug"),
        ]
    dirs, files = vfs.count()
    text = f"VFS '{vfs.name}' загружена в память: папок {dirs}, файлов {files}"
    return vfs, [(text, "debug")]


def main():
    """Читает параметры, загружает VFS, печатает их и запускает окно."""
    config = parse_args()
    vfs, notes = load_vfs_notes(config)
    for line in config.debug_lines():
        print(line)
    for text, _tag in notes:
        print(f"[debug] {text}")
    run(config, Shell(vfs), notes)


if __name__ == "__main__":
    main()
