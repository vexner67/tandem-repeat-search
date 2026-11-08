# Консольный ввод, разбор аргументов и вывод результатов.

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tandem_repeat.application.search import SearchService, SourceError
from tandem_repeat.infrastructure.sources import (
    FileSource,
    StringSource,
    URLSource,
)


class Console:
    # Консольный интерфейс проверки слова и поиска повторов.

    def __init__(self, service: SearchService) -> None:
        self.service = service

    def run(self, argv: Sequence[str] | None = None) -> int:
        # Коды выхода: 0 при успехе, 1 при несовпадении, 2 при ошибке.
        parser = argparse.ArgumentParser(
            description="Проверка и поиск слов из двух одинаковых частей."
        )
        sources = parser.add_mutually_exclusive_group()
        sources.add_argument("--text", help="Текст для поиска")
        sources.add_argument(
            "--file", type=Path, help="Путь к текстовому файлу"
        )
        sources.add_argument("--url", help="URL страницы HTTP(S)")
        sources.add_argument("--check", help="Проверить одно слово целиком")
        parser.add_argument(
            "--encoding", default="utf-8-sig", help="Кодировка файла (UTF-8)"
        )
        args = parser.parse_args(argv)

        if args.check is not None:
            valid = self.service.check(args.check)
            print("Тандемный повтор." if valid else "Не тандемный повтор.")
            return 0 if valid else 1

        try:
            if args.file is not None:
                source = FileSource(args.file, args.encoding)
            elif args.url is not None:
                source = URLSource(args.url)
            else:
                text = args.text
                if text is None:
                    text = input("Введите текст: ")
                source = StringSource(text)
            matches = self.service.search(source)
        except (SourceError, EOFError, KeyboardInterrupt) as error:
            print(f"Ошибка ввода: {error}", file=sys.stderr)
            return 2

        print(f"Найдено: {len(matches)}")
        for match in matches:
            print(
                f"{match.word} = {match.half} + {match.half} "
                f"[{match.start}:{match.end}]"
            )
        return 0
