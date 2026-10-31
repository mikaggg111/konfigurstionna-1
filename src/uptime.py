"""Команда uptime: сколько времени работает эмулятор."""
"""выполняет её над деревом из vfs.py"""
import time
from typing import List, Tuple

from errors import ShellError
from options import split_options

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
ONE = 1
PRETTY_FLAG = "p"
SINCE_FLAG = "s"
UPTIME_OPTIONS = PRETTY_FLAG + SINCE_FLAG
TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
USERS_TEXT = "1 user"


def plural(count: int, one: str, many: str) -> str:
    """Возвращает слово в нужной форме: 1 day, 2 days."""
    return one if count == ONE else many


def split_duration(seconds: float) -> Tuple[int, int, int]:
    """Раскладывает секунды на (дни, часы, минуты); секунды отбрасываются."""
    total_minutes = int(max(seconds, 0) // SECONDS_PER_MINUTE)
    total_hours, minutes = divmod(total_minutes, MINUTES_PER_HOUR)
    days, hours = divmod(total_hours, HOURS_PER_DAY)
    return days, hours, minutes


def short_form(seconds: float) -> str:
    """Короткая запись, как у uptime: 5 min, 2:03, 1 day, 3:04."""
    days, hours, minutes = split_duration(seconds)
    if days:
        return f"{days} {plural(days, 'day', 'days')}, {hours}:{minutes:02d}"
    if hours:
        return f"{hours}:{minutes:02d}"
    return f"{minutes} min"


def pretty_form(seconds: float) -> str:
    """Запись для uptime -p: up 1 day, 2 hours, 3 minutes."""
    days, hours, minutes = split_duration(seconds)
    units = ((days, "day", "days"), (hours, "hour", "hours"),
             (minutes, "minute", "minutes"))
    parts = [f"{value} {plural(value, one, many)}"
             for value, one, many in units if value]
    return "up " + ", ".join(parts or ["0 minutes"])


def cmd_uptime(args: List[str], start: float, now: float) -> str:
    """uptime [-p | -s] - время работы эмулятора.

    start - момент запуска, now - текущий момент (в секундах).
    """
    flags, operands = split_options(args, UPTIME_OPTIONS)
    if operands:
        raise ShellError(f"extra operand '{operands[0]}'")
    if flags == set(UPTIME_OPTIONS):
        raise ShellError("options -p and -s cannot be used together")
    if SINCE_FLAG in flags:
        return time.strftime(DATE_FORMAT, time.localtime(start))
    if PRETTY_FLAG in flags:
        return pretty_form(now - start)
    clock = time.strftime(TIME_FORMAT, time.localtime(now))
    return f" {clock} up {short_form(now - start)},  {USERS_TEXT}"
