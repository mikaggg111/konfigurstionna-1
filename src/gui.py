"""Графический интерфейс эмулятора на tkinter."""
import getpass
import socket
import tkinter as tk
from tkinter import scrolledtext
from typing import List, Optional, Tuple

from config import Config
from errors import ShellError
from script import load_script
from shell import Result, Shell

Note = Tuple[str, str]

FONT = ("Courier New", 11)
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
ERROR_COLOR = "#f48771"
PROMPT_COLOR = "#6a9955"
DEBUG_COLOR = "#808080"
WINDOW_SIZE = "800x500"
SCRIPT_DELAY_MS = 300


class EmulatorApp:
    """Главное окно эмулятора: область вывода и строка ввода."""

    def __init__(self, root: tk.Tk, shell: Shell, config: Config,
                 notes: Optional[List[Note]] = None):
        """Создаёт виджеты, печатает параметры и запускает скрипт."""
        self.root = root
        self.shell = shell
        self.config = config
        self.script_lines = []
        self.script_index = 0
        self.script_running = False
        user = getpass.getuser()
        host = socket.gethostname()
        self.login = f"{user}@{host}"
        root.title(f"Эмулятор - [{user}@{host}]")
        self._build_widgets()
        self._print_debug()
        for text, tag in notes or []:
            self.print_text(text, tag)
        self._start_script()

    def _build_widgets(self):
        """Строит область вывода и поле ввода."""
        self.output = scrolledtext.ScrolledText(
            self.root, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self.output.tag_config("error", foreground=ERROR_COLOR)
        self.output.tag_config("prompt", foreground=PROMPT_COLOR)
        self.output.tag_config("debug", foreground=DEBUG_COLOR)
        bottom = tk.Frame(self.root, bg=BG_COLOR)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.output.pack(fill=tk.BOTH, expand=True)
        self.prompt_label = tk.Label(
            bottom, font=FONT, bg=BG_COLOR, fg=PROMPT_COLOR,
        )
        self.prompt_label.pack(side=tk.LEFT)
        self.entry = tk.Entry(
            bottom, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            insertbackground=FG_COLOR, borderwidth=0,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._update_prompt()
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()

    def print_text(self, text: str, tag: str = ""):
        """Добавляет строку текста в область вывода."""
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n", tag)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def _prompt(self) -> str:
        """Приглашение вида "user@host:/текущая/папка$ " (папка из VFS)."""
        return f"{self.login}:{self.shell.vfs.cwd_path()}$ "

    def _update_prompt(self):
        """Показывает слева от поля ввода, в какой папке мы находимся."""
        self.prompt_label.configure(text=self._prompt())

    def _clear_screen(self):
        """Стирает весь текст в области вывода (команда clear)."""
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

    def _print_debug(self):
        """Печатает все заданные параметры запуска (отладочный вывод)."""
        for line in self.config.debug_lines():
            self.print_text(line, "debug")

    def _execute_line(self, line: str) -> Result:
        """Показывает команду, выполняет её и показывает результат."""
        self.print_text(self._prompt() + line, "prompt")
        result = self.shell.execute(line)
        if result.output:
            self.print_text(result.output)
        if result.error:
            self.print_text(result.error, "error")
        if result.clear:
            self._clear_screen()
        self._update_prompt()
        return result

    def _on_enter(self, _event):
        """Обрабатывает нажатие Enter: выполняет введённую команду."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        result = self._execute_line(line)
        if result.should_exit:
            self.root.destroy()

    def _start_script(self):
        """Читает стартовый скрипт и запускает его выполнение."""
        path = self.config.script_path
        if not path:
            return
        try:
            self.script_lines = load_script(path)
        except ShellError as error:
            self.print_text(f"Ошибка: {error}", "error")
            return
        self.print_text(f"--- Выполнение скрипта {path} ---", "debug")
        self.script_running = True
        self.entry.configure(state=tk.DISABLED)
        self.root.after(SCRIPT_DELAY_MS, self._run_next_line)

    def _run_next_line(self):
        """Выполняет очередную строку скрипта или завершает скрипт."""
        if self.script_index >= len(self.script_lines):
            self._finish_script("--- Скрипт завершён ---", "debug")
            return
        number, line = self.script_lines[self.script_index]
        self.script_index += 1
        result = self._execute_line(line)
        if result.should_exit:
            self.root.destroy()
            return
        if result.error:
            text = f"--- Скрипт остановлен: ошибка в строке {number} ---"
            self._finish_script(text, "error")
            return
        self.root.after(SCRIPT_DELAY_MS, self._run_next_line)

    def _finish_script(self, message: str, tag: str):
        """Сообщает об окончании скрипта и снова включает ввод."""
        self.print_text(message, tag)
        self.script_running = False
        self.entry.configure(state=tk.NORMAL)
        self.entry.focus_set()


def run(config: Config, shell: Shell, notes: Optional[List[Note]] = None):
    """Запускает главный цикл GUI с заданными параметрами."""
    root = tk.Tk()
    root.geometry(WINDOW_SIZE)
    EmulatorApp(root, shell, config, notes)
    root.mainloop()
