# Контракт пользовательского интерфейса приложения.

from collections.abc import Sequence
from typing import Protocol


class Application(Protocol):
    # Запускает выбранный интерфейс и возвращает код завершения.

    def run(self, argv: Sequence[str] | None = None) -> int: ...
