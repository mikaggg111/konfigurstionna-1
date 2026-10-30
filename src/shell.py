"""Ядро эмулятора: выполнение команд без привязки к GUI."""
from dataclasses import dataclass
from typing import Callable, Dict, List

from cmd_parser import parse_line


@dataclass
class Result:
    """Результат выполнения команды."""

    output: str = ""
    error: str = ""
    should_exit: bool = False


class Shell:
    """Интерпретатор команд эмулятора."""

    def __init__(self):
        """Регистрирует поддерживаемые команды."""
        self._commands: Dict[str, Callable[[List[str]], Result]] = {
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "exit": self._cmd_exit,
        }

    def execute(self, line: str) -> Result:
        """Разбирает строку и выполняет соответствующую команду."""
        parsed = parse_line(line)
        if parsed is None:
            return Result()
        handler = self._commands.get(parsed.name)
        if handler is None:
            return Result(error=f"{parsed.name}: command not found")
        return handler(parsed.args)

    @staticmethod
    def _stub(name: str, args: List[str]) -> Result:
        """Формирует вывод заглушки: имя команды и её аргументы."""
        return Result(output=f"{name} args: {args}")

    def _cmd_ls(self, args: List[str]) -> Result:
        """Заглушка команды ls."""
        return self._stub("ls", args)

    def _cmd_cd(self, args: List[str]) -> Result:
        """Заглушка команды cd."""
        return self._stub("cd", args)

    @staticmethod
    def _cmd_exit(args: List[str]) -> Result:
        """Команда exit: завершает работу эмулятора."""
        if args:
            return Result(error="exit: too many arguments")
        return Result(should_exit=True)
