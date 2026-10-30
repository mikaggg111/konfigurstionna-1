"""Точка входа эмулятора командной строки."""
from config import parse_args
from gui import run


def main():
    """Читает параметры, печатает их в консоль и запускает окно."""
    config = parse_args()
    for line in config.debug_lines():
        print(line)
    run(config)


if __name__ == "__main__":
    main()
