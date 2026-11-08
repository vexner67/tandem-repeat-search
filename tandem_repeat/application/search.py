# Контракты и сценарии проверки слова и поиска в тексте.

from dataclasses import dataclass
from typing import Protocol

from tandem_repeat.domain.tandem import TandemMatch


class SourceError(Exception):
    # Источник не смог предоставить текст.
    pass


class TextSource(Protocol):
    # Контракт источника текста.

    def read(self) -> str:
        # Возвращает текст; при ошибке чтения вызывает SourceError.
        ...


class TandemMatcher(Protocol):
    # Проверяет слова и находит повторы по одному правилу.

    def is_tandem(self, word: str) -> bool:
        # Проверяет, состоит ли все слово из двух одинаковых частей.
        ...

    def find_tandems(self, text: str) -> list[TandemMatch]:
        # Возвращает вхождения в порядке появления, сохраняя дубликаты.
        ...


@dataclass(frozen=True)
class SearchService:
    # Получает распознаватель при создании, а источник при поиске.

    matcher: TandemMatcher

    def check(self, word: str) -> bool:
        # Передает слово распознавателю, сохраняя пробелы и регистр.
        return self.matcher.is_tandem(word)

    def search(self, source: TextSource) -> list[TandemMatch]:
        # Читает источник один раз и передает текст распознавателю.
        text = source.read()
        return self.matcher.find_tandems(text)
