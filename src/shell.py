"""Ядро эмулятора: выполнение команд без привязки к GUI."""
from dataclasses import dataclass
from typing import Callable, Dict, List

from cmd_parser import parse_line  # наш парсер из файла cmd_parser.py


# хранит результат выполнения: вывод, ошибку и флаг "выйти"
@dataclass
class Result:
    """Результат выполнения команды."""

    output: str = ""  # обычный текст для пользователя
    error: str = ""  # текст ошибки (окно покажет его красным)
    should_exit: bool = False  # True - нужно закрыть эмулятор (для exit)


# "мозг" эмулятора: принимает строку и выполняет команду
class Shell:
    """Интерпретатор команд эмулятора."""

    def __init__(self):
        """Регистрирует поддерживаемые команды."""
        # Поле _commands - словарь: имя команды -> метод, который её
        # выполняет. Callable[[List[str]], Result] - это метод, который
        # принимает список строк и возвращает Result.
        # Новую команду добавим одной строкой здесь.
        self._commands: Dict[str, Callable[[List[str]], Result]] = {
            "ls": self._cmd_ls,  # команда ls
            "cd": self._cmd_cd,  # команда cd
            "exit": self._cmd_exit,  # команда exit
        }

    # принимает строку, которую ввёл пользователь
    def execute(self, line: str) -> Result:
        """Разбирает строку и выполняет соответствующую команду."""
        parsed = parse_line(line)  # делим строку на команду и аргументы
        if parsed is None:  # пустой ввод
            return Result()  # ничего не делаем, пустой результат
        # ищем в словаре метод по имени команды, если нет - будет None
        handler = self._commands.get(parsed.name)
        if handler is None:  # такой команды нет в словаре
            return Result(error=f"{parsed.name}: command not found")  # ошибка
        return handler(parsed.args)  # вызываем метод команды с аргументами

    @staticmethod  # заглушки: метод не использует self
    def _stub(name: str, args: List[str]) -> Result:
        """Формирует вывод заглушки: имя команды и её аргументы."""
        return Result(output=f"{name} args: {args}")  # общий код для ls и cd

    # метод _cmd_ls принимает args (список строк) и возвращает Result
    def _cmd_ls(self, args: List[str]) -> Result:
        """Заглушка команды ls."""
        return self._stub("ls", args)  # передаём _stub имя ls и аргументы

    def _cmd_cd(self, args: List[str]) -> Result:
        """Заглушка команды cd."""
        return self._stub("cd", args)  # пока только имя и аргументы

    @staticmethod
    def _cmd_exit(args: List[str]) -> Result:
        """Команда exit: завершает работу эмулятора."""
        if args:  # у exit не должно быть аргументов
            return Result(error="exit: too many arguments")  # ошибка
        return Result(should_exit=True)  # сообщаем окну, что нужно закрыться
