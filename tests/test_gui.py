"""Тесты окна: параметры и стартовый скрипт (нужен дисплей)."""
import os
import tempfile
import time
import unittest
from unittest import mock

import _path

try:
    import tkinter as tk
except ImportError:
    tk = None

if tk is not None:
    import gui
    from config import Config
    from shell import Shell

WAIT_LIMIT_S = 5
FAST_DELAY_MS = 1


class GuiTest(unittest.TestCase):
    """Проверяет окно: заголовок, отладочный вывод, скрипт."""

    def setUp(self):
        """Создаёт скрытое окно или пропускает тест, если нет дисплея."""
        if tk is None:
            self.skipTest("tkinter не установлен")
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("нет дисплея")
        self.root.withdraw()
        patcher = mock.patch.object(gui, "SCRIPT_DELAY_MS", FAST_DELAY_MS)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.close_root)

    def close_root(self):
        """Закрывает окно, если его ещё не закрыла команда exit."""
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def open_app(self, **params):
        """Создаёт приложение с заданными параметрами запуска."""
        return gui.EmulatorApp(self.root, Shell(), Config(**params))

    def wait_script(self, app):
        """Крутит цикл окна, пока скрипт не закончится."""
        deadline = time.time() + WAIT_LIMIT_S
        while app.script_running and time.time() < deadline:
            self.root.update()
        self.assertFalse(app.script_running, "скрипт не закончился")

    @staticmethod
    def screen(app):
        """Возвращает весь текст из области вывода."""
        return app.output.get("1.0", tk.END)

    def script_file(self, text):
        """Создаёт временный скрипт и возвращает его путь."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_title_has_user_and_host(self):
        """Заголовок вида «Эмулятор - [user@host]»."""
        self.open_app()
        title = self.root.title()
        self.assertTrue(title.startswith("Эмулятор - ["))
        self.assertIn("@", title)

    def test_debug_output_of_params(self):
        """При запуске в окне видны все заданные параметры."""
        app = self.open_app(vfs_path="x.csv")
        text = self.screen(app)
        self.assertIn("x.csv", text)
        self.assertIn("--script", text)

    def test_script_shows_input_and_output(self):
        """Скрипт показывает и команды, и их вывод."""
        path = self.script_file("ls -l\ncd /a\n")
        app = self.open_app(script_path=path)
        self.wait_script(app)
        text = self.screen(app)
        self.assertIn("$ ls -l", text)
        self.assertIn("ls args: ['-l']", text)
        self.assertIn("cd args: ['/a']", text)
        self.assertIn("Скрипт завершён", text)

    def test_script_stops_on_first_error(self):
        """После первой ошибки остальные строки не выполняются."""
        path = self.script_file("ls\nfoo\ncd /never\n")
        app = self.open_app(script_path=path)
        self.wait_script(app)
        text = self.screen(app)
        self.assertIn("foo: command not found", text)
        self.assertIn("ошибка в строке 2", text)
        self.assertNotIn("/never", text)

    def test_missing_script(self):
        """Нет файла скрипта - сообщение об ошибке, ввод доступен."""
        app = self.open_app(script_path="no_such_script.txt")
        self.assertIn("не удалось прочитать", self.screen(app))
        self.assertEqual(str(app.entry.cget("state")), tk.NORMAL)

    def test_input_returns_after_script(self):
        """После скрипта можно вводить команды вручную."""
        path = self.script_file("ls\n")
        app = self.open_app(script_path=path)
        self.wait_script(app)
        self.assertEqual(str(app.entry.cget("state")), tk.NORMAL)


if __name__ == "__main__":
    unittest.main()
