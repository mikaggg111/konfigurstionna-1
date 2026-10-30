"""Ядро эмулятора: выполнение команд без привязки к GUI."""
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from cmd_parser import parse_line
from commands import cmd_cd, cmd_ls, cmd_tac
from errors import ShellError
from uptime import cmd_uptime
from vfs import Vfs


@dataclass
class Result:
    """Результат выполнения команды."""

    output: str = ""
    error: str = ""
    should_exit: bool = False
    clear: bool = False


def no_args(args: List[str]):
    """Выбрасывает ошибку, если команде без аргументов их передали."""
    if args:
        raise ShellError("too many arguments")


class Shell:
    """Интерпретатор команд эмулятора."""

    def __init__(self, vfs: Optional[Vfs] = None,
                 clock: Callable[[], float] = time.time):
        """Запоминает VFS и время запуска, регистрирует команды."""
        self.vfs = vfs or Vfs()
        self._clock = clock
        self._start = clock()
        self._commands: Dict[str, Callable[[List[str]], Result]] = {
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "tac": self._cmd_tac,
            "clear": self._cmd_clear,
            "uptime": self._cmd_uptime,
            "exit": self._cmd_exit,
            "vfsinfo": self._cmd_vfsinfo,
        }

    def execute(self, line: str) -> Result:
        """Разбирает строку и выполняет соответствующую команду."""
        parsed = parse_line(line)
        if parsed is None:
            return Result()
        handler = self._commands.get(parsed.name)
        if handler is None:
            return Result(error=f"{parsed.name}: command not found")
        try:
            return handler(parsed.args)
        except ShellError as error:
            return Result(error=f"{parsed.name}: {error}")

    def _cmd_ls(self, args: List[str]) -> Result:
        """ls [-l] [путь...]: содержимое папок и файлов."""
        return Result(output=cmd_ls(self.vfs, args))

    def _cmd_cd(self, args: List[str]) -> Result:
        """cd [путь]: смена текущей папки."""
        return Result(output=cmd_cd(self.vfs, args))

    def _cmd_tac(self, args: List[str]) -> Result:
        """tac файл...: строки файлов в обратном порядке."""
        return Result(output=cmd_tac(self.vfs, args))

    @staticmethod
    def _cmd_clear(args: List[str]) -> Result:
        """clear: просит окно очистить экран."""
        no_args(args)
        return Result(clear=True)

    def _cmd_uptime(self, args: List[str]) -> Result:
        """uptime [-p | -s]: время работы эмулятора."""
        return Result(output=cmd_uptime(args, self._start, self._clock()))

    @staticmethod
    def _cmd_exit(args: List[str]) -> Result:
        """exit: завершает работу эмулятора."""
        no_args(args)
        return Result(should_exit=True)

    def _cmd_vfsinfo(self, args: List[str]) -> Result:
        """Служебная команда: имя загруженной VFS и число её элементов."""
        no_args(args)
        dirs, files = self.vfs.count()
        return Result(output=f"VFS: {self.vfs.name}, папок: {dirs}, "
                             f"файлов: {files}")
