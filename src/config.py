"""Параметры командной строки эмулятора."""
import argparse
from dataclasses import dataclass
from typing import List, Optional

NOT_SET = "<не задан>"


@dataclass
class Config:
    """Параметры, с которыми запущен эмулятор."""

    vfs_path: Optional[str] = None
    script_path: Optional[str] = None

    def debug_lines(self) -> List[str]:
        """Возвращает строки отладочного вывода всех параметров."""
        return [
            "[debug] Параметры запуска:",
            f"[debug]   --vfs    = {self.vfs_path or NOT_SET}",
            f"[debug]   --script = {self.script_path or NOT_SET}",
        ]


def parse_args(argv: Optional[List[str]] = None) -> Config:
    """Разбирает параметры командной строки в объект Config."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки UNIX")

    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")

    args = parser.parse_args(argv)
    return Config(vfs_path=args.vfs, script_path=args.script)
