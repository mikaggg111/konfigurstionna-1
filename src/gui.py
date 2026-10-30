"""Графический интерфейс эмулятора на tkinter."""
import getpass
import socket
import tkinter as tk
from tkinter import scrolledtext

from shell import Shell

FONT = ("Courier New", 11)
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d4d4d4"
ERROR_COLOR = "#f48771"
PROMPT_COLOR = "#6a9955"
WINDOW_SIZE = "800x500"


class EmulatorApp:
    """Главное окно эмулятора: область вывода и строка ввода."""

    def __init__(self, root: tk.Tk, shell: Shell):
        """Создаёт виджеты и привязывает обработчики."""
        self.root = root
        self.shell = shell
        user = getpass.getuser()
        host = socket.gethostname()
        self.prompt = f"{user}@{host}:~$ "
        root.title(f"Эмулятор - [{user}@{host}]")
        self._build_widgets()

    def _build_widgets(self):
        """Строит область вывода и поле ввода."""
        self.output = scrolledtext.ScrolledText(
            self.root, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            state=tk.DISABLED, wrap=tk.WORD,
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.tag_config("error", foreground=ERROR_COLOR)
        self.output.tag_config("prompt", foreground=PROMPT_COLOR)
        self.entry = tk.Entry(
            self.root, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            insertbackground=FG_COLOR,
        )
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()

    def print_text(self, text: str, tag: str = ""):
        """Добавляет строку текста в область вывода."""
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n", tag)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def _on_enter(self, _event):
        """Обрабатывает нажатие Enter: выполняет введённую команду."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.print_text(self.prompt + line, "prompt")
        result = self.shell.execute(line)
        if result.output:
            self.print_text(result.output)
        if result.error:
            self.print_text(result.error, "error")
        if result.should_exit:
            self.root.destroy()


def run():
    """Запускает главный цикл GUI."""
    root = tk.Tk()
    root.geometry(WINDOW_SIZE)
    EmulatorApp(root, Shell())
    root.mainloop()
