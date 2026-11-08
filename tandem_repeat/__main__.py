# Создание зависимостей и запуск консольного интерфейса.

import sys
from collections.abc import Sequence
from pathlib import Path

if not __package__:
    # При запуске файла Python ищет пакет относительно корня проекта.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tandem_repeat.application.search import SearchService
from tandem_repeat.domain.tandem import RegexTandemMatcher
from tandem_repeat.presentation.console import Console


def main(argv: Sequence[str] | None = None) -> int:
    service = SearchService(matcher=RegexTandemMatcher())
    console = Console(service)
    return console.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
