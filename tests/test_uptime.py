"""Тесты команды uptime."""
import time
import unittest

from shell import Shell
from uptime import DATE_FORMAT, pretty_form, short_form

START = 1_000_000_000.0
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR


class FormatTest(unittest.TestCase):
    """Форматы времени работы."""

    def test_short_form(self):
        """Короткая форма: минуты, часы:минуты, дни."""
        self.assertEqual(short_form(0), "0 min")
        self.assertEqual(short_form(5 * MINUTE + 59), "5 min")
        self.assertEqual(short_form(3 * HOUR + 4 * MINUTE), "3:04")
        self.assertEqual(short_form(DAY + 2 * HOUR + 3 * MINUTE),
                         "1 day, 2:03")
        self.assertEqual(short_form(2 * DAY), "2 days, 0:00")

    def test_pretty_form(self):
        """Форма для -p: единицы словами, нулевые пропускаются."""
        self.assertEqual(pretty_form(0), "up 0 minutes")
        self.assertEqual(pretty_form(MINUTE), "up 1 minute")
        self.assertEqual(pretty_form(DAY + HOUR + MINUTE),
                         "up 1 day, 1 hour, 1 minute")
        self.assertEqual(pretty_form(2 * DAY + 5 * MINUTE),
                         "up 2 days, 5 minutes")


class UptimeCommandTest(unittest.TestCase):
    """Команда uptime в Shell с поддельными часами."""

    def setUp(self):
        """Создаёт Shell, у которого время задаётся вручную."""
        self.now = START
        self.shell = Shell(clock=lambda: self.now)

    def run_cmd(self, line):
        """Выполняет команду и возвращает Result."""
        return self.shell.execute(line)

    def test_default(self):
        """Обычный режим: время суток, сколько работает, один пользователь."""
        self.now = START + 5 * MINUTE
        output = self.run_cmd("uptime").output
        self.assertIn(" up 5 min,  1 user", output)

    def test_pretty(self):
        """uptime -p."""
        self.now = START + 2 * HOUR + 30 * MINUTE
        self.assertEqual(self.run_cmd("uptime -p").output,
                         "up 2 hours, 30 minutes")

    def test_since(self):
        """uptime -s: когда запущен эмулятор."""
        expected = time.strftime(DATE_FORMAT, time.localtime(START))
        self.assertEqual(self.run_cmd("uptime -s").output, expected)

    def test_extra_operand(self):
        """Лишний операнд."""
        self.assertEqual(self.run_cmd("uptime x").error,
                         "uptime: extra operand 'x'")

    def test_bad_option(self):
        """Неизвестная опция."""
        self.assertEqual(self.run_cmd("uptime -z").error,
                         "uptime: invalid option -- 'z'")

    def test_conflicting_options(self):
        """-p и -s вместе нельзя."""
        self.assertIn("cannot be used together",
                      self.run_cmd("uptime -ps").error)


if __name__ == "__main__":
    unittest.main()
