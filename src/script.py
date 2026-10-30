"""Чтение стартового скрипта эмулятора."""
from typing import List, Tuple

from errors import ShellError

COMMENT_SIGN = "#"


def strip_comment(line: str) -> str:
    """Убирает комментарий (всё после #) и пробелы по краям строки."""
    return line.split(COMMENT_SIGN, 1)[0].strip()


def load_script(path: str) -> List[Tuple[int, str]]:
    """Читает скрипт и возвращает пары (номер строки, команда).

    Пустые строки и комментарии пропускаются. Номера строк нужны,
    чтобы сообщить, на какой строке скрипт остановился.
    """
    try:
        with open(path, encoding="utf-8-sig") as file:
            lines = file.read().splitlines()
    except OSError as error:
        raise ShellError(
            f"не удалось прочитать скрипт '{path}': {error.strerror}"
        ) from error
    except ValueError as error:
        raise ShellError(f"скрипт '{path}' не в кодировке UTF-8") from error
    result = []
    for number, line in enumerate(lines, start=1):
        command = strip_comment(line)
        if command:
            result.append((number, command))
    return result
