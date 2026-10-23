"""Простой парсер ввода: делит строку на команду и аргументы."""
from dataclasses import dataclass, field  # dataclass - класс для данных
from typing import List, Optional  # подсказки типов: список и "или None"


# хранит результат разбора: имя команды и список аргументов
# @dataclass сам создаёт конструктор ParsedCommand(name, args)
@dataclass
class ParsedCommand:
    """Результат разбора строки: имя команды и список аргументов."""

    name: str  # имя команды, например "ls"
    # аргументы, например ["-l", "/tmp"]. Если при создании объекта args
    # не передали, default_factory=list создаст для него новый пустой список
    args: List[str] = field(default_factory=list)


# принимает строку, которую ввёл пользователь, и возвращает разобранную
# команду (ParsedCommand) или None, если ничего не ввели
def parse_line(line: str) -> Optional[ParsedCommand]:
    """Разделяет строку по пробелам на команду и аргументы.

    Возвращает None, если строка пустая или состоит из пробелов.
    """
    parts = line.split()  # режет по пробелам: "  ls  -l " -> ["ls", "-l"]
    if not parts:  # список пустой - пользователь ничего не ввёл
        return None  # команды нет
    # 1-е слово - команда, все остальные слова - её аргументы
    return ParsedCommand(name=parts[0], args=parts[1:])
