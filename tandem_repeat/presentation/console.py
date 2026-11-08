# Консольный ввод, разбор аргументов и вывод результатов.

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tandem_repeat.application.search import (
    SearchService,
    SourceError,
    TextSource,
)
from tandem_repeat.domain.tandem import TandemMatch
from tandem_repeat.infrastructure.sources import (
    FileSource,
    StringSource,
    URLSource,
)
from tandem_repeat.presentation import Application


class Console(Application):
    # Консольный интерфейс проверки слова и поиска повторов.

    def __init__(self, service: SearchService) -> None:
        self.service = service

    def run(self, argv: Sequence[str] | None = None) -> int:
        # Коды выхода: 0 при успехе, 1 при несовпадении, 2 при ошибке.
        arguments = _parse_arguments(argv)
        if arguments.check is not None:
            return self._check_word(arguments.check)

        try:
            source = _select_source(arguments)
            matches = self.service.search(source)
        except (SourceError, EOFError, KeyboardInterrupt) as error:
            print(f"Ошибка ввода: {error}", file=sys.stderr)
            return 2

        _print_matches(matches)
        return 0

    def _check_word(self, word: str) -> int:
        valid = self.service.check(word)
        print("Тандемный повтор." if valid else "Не тандемный повтор.")
        return 0 if valid else 1


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Проверка и поиск слов из двух одинаковых частей."
    )
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--text", help="Текст для поиска")
    sources.add_argument("--file", type=Path, help="Путь к текстовому файлу")
    sources.add_argument("--url", help="URL страницы HTTP(S)")
    sources.add_argument("--check", help="Проверить одно слово целиком")
    parser.add_argument(
        "--encoding", default="utf-8-sig", help="Кодировка файла (UTF-8)"
    )
    return parser.parse_args(argv)


def _select_source(arguments: argparse.Namespace) -> TextSource:
    if arguments.file is not None:
        return FileSource(arguments.file, arguments.encoding)
    if arguments.url is not None:
        return URLSource(arguments.url)
    text = arguments.text
    if text is None:
        text = input("Введите текст: ")
    return StringSource(text)


def _print_matches(matches: list[TandemMatch]) -> None:
    print(f"Найдено: {len(matches)}")
    for match in matches:
        print(
            f"{match.word} = {match.half} + {match.half} "
            f"[{match.start}:{match.end}]"
        )
