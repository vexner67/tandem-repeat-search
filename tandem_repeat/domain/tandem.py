# Поиск повторов из русских и латинских букв с учетом регистра.

import re
from dataclasses import dataclass

ALPHABET = r"A-Za-zА-Яа-яЁё"
WORD_PATTERN = re.compile(rf"(?P<half>[{ALPHABET}]+)(?P=half)")
SEARCH_PATTERN = re.compile(rf"(?<!\w){WORD_PATTERN.pattern}(?!\w)")


@dataclass(frozen=True)
class TandemMatch:
    # Слово, его половина и позиции [start:end] с отсчетом от нуля.

    word: str
    half: str
    start: int
    end: int


class RegexTandemMatcher:
    # Распознает слова формы XX с помощью обратной ссылки в regex.

    def is_tandem(self, word: str) -> bool:
        # Проверяет форму XX, где X непусто; сохраняет пробелы и регистр.
        return WORD_PATTERN.fullmatch(word) is not None

    def find_tandems(self, text: str) -> list[TandemMatch]:
        # Находит целые слова в порядке появления, сохраняя дубликаты.
        return [
            TandemMatch(
                word=match.group(0),
                half=match.group("half"),
                start=match.start(),
                end=match.end(),
            )
            for match in SEARCH_PATTERN.finditer(text)
        ]
