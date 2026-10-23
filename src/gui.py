"""Графический интерфейс эмулятора на tkinter."""
import getpass  # имя пользователя ОС
import socket  # имя компьютера
import tkinter as tk  # библиотека для окон (входит в Python)
from tkinter import scrolledtext  # текстовое поле с прокруткой

from shell import Shell

VFS_NAME = "default"  # имя VFS для заголовка (пока VFS нет)
FONT = ("Courier New", 11)  # шрифт: название и размер
BG_COLOR = "#1e1e1e"  # цвет фона
FG_COLOR = "#d4d4d4"  # цвет обычного текста
ERROR_COLOR = "#f48771"  # цвет ошибок (красный)
PROMPT_COLOR = "#6a9955"  # цвет приглашения (зелёный)
WINDOW_SIZE = "800x500"  # размер окна: ширина x высота в пикселях


# окно: рисует виджеты и реагирует на Enter
class EmulatorApp:
    """Главное окно эмулятора: область вывода и строка ввода."""

    def __init__(self, root: tk.Tk, shell: Shell):
        """Создаёт виджеты и привязывает обработчики."""
        self.root = root  # запоминаем окно, чтобы потом его закрыть
        self.shell = shell  # запоминаем Shell: он выполняет команды
        user = getpass.getuser()  # имя пользователя из реальной ОС
        host = socket.gethostname()  # имя компьютера из реальной ОС
        # приглашение вида "имя_пользователя@имя_компьютера:~$ "
        self.prompt = f"{user}@{host}:~$ "
        root.title(f"Эмулятор - [VFS: {VFS_NAME}]")  # заголовок с именем VFS
        self._build_widgets()  # строим вид (поля выше уже заполнены)

    def _build_widgets(self):
        """Строит область вывода и поле ввода."""
        self.output = scrolledtext.ScrolledText(  # область вывода с прокруткой
            self.root, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            state=tk.DISABLED, wrap=tk.WORD,  # нельзя печатать; перенос слов
        )
        self.output.pack(fill=tk.BOTH, expand=True)  # занять всё место
        self.output.tag_config("error", foreground=ERROR_COLOR)  # красный
        self.output.tag_config("prompt", foreground=PROMPT_COLOR)  # зелёный
        self.entry = tk.Entry(  # строка ввода: сюда печатаем команды
            self.root, font=FONT, bg=BG_COLOR, fg=FG_COLOR,
            insertbackground=FG_COLOR,  # цвет курсора (иначе он невидим)
        )
        self.entry.pack(fill=tk.X)  # растянуть по ширине окна
        self.entry.bind("<Return>", self._on_enter)  # Enter -> _on_enter
        self.entry.focus_set()  # курсор сразу в строке ввода

    def print_text(self, text: str, tag: str = ""):
        """Добавляет строку текста в область вывода."""
        self.output.configure(state=tk.NORMAL)  # разблокируем (иначе нельзя)
        self.output.insert(tk.END, text + "\n", tag)  # в конец, с новой строки
        self.output.configure(state=tk.DISABLED)  # блокируем от ручных правок
        self.output.see(tk.END)  # прокрутка вниз к последней строке

    def _on_enter(self, _event):
        """Обрабатывает нажатие Enter: выполняет введённую команду."""
        line = self.entry.get()  # берём текст из строки ввода
        self.entry.delete(0, tk.END)  # очищаем строку ввода
        self.print_text(self.prompt + line, "prompt")  # показываем команду
        result = self.shell.execute(line)  # Shell выполняет, вернёт Result
        if result.output:  # есть обычный вывод
            self.print_text(result.output)  # показываем его
        if result.error:  # есть ошибка
            self.print_text(result.error, "error")  # показываем красным
        if result.should_exit:  # команда exit просила выйти
            self.root.destroy()  # закрываем окно


def run():
    """Запускает главный цикл GUI."""
    root = tk.Tk()  # создаём главное окно
    root.geometry(WINDOW_SIZE)  # задаём размер окна
    EmulatorApp(root, Shell())  # приложение: окно + новый Shell
    root.mainloop()  # цикл: окно ждёт действий, пока его не закроют
