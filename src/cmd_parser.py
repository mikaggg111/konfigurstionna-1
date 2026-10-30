"""Простой парсер ввода: делит строку на команду и аргументы."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParsedCommand:
    """Результат разбора строки: имя команды и список аргументов."""

    name: str
    args: List[str] = field(default_factory=list)


def parse_line(line: str) -> Optional[ParsedCommand]:
    """Разделяет строку по пробелам на команду и аргументы.

    Возвращает None, если строка пустая или состоит из пробелов.
    """
    parts = line.split()
    if not parts:
        return None
    return ParsedCommand(name=parts[0], args=parts[1:])
