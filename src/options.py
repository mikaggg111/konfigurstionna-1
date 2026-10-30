"""Разбор опций команд (-l, -r) в стиле UNIX."""
from typing import List, Set, Tuple

from errors import ShellError

OPTION_PREFIX = "-"


def split_options(args: List[str],
                  allowed: str) -> Tuple[Set[str], List[str]]:
    """Отделяет опции от остальных аргументов (операндов).

    allowed - строка допустимых букв опций, например "lr". Можно писать
    опции слитно (-lr). Возвращает (множество букв, список операндов).
    Одиночный "-" считается обычным операндом.
    """
    flags: Set[str] = set()
    operands: List[str] = []
    for arg in args:
        if arg != OPTION_PREFIX and arg.startswith(OPTION_PREFIX):
            for letter in arg[1:]:
                if letter not in allowed:
                    raise ShellError(f"invalid option -- '{letter}'")
                flags.add(letter)
        else:
            operands.append(arg)
    return flags, operands
