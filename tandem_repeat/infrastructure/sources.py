# Чтение источников с ограничением размера и извлечение текста HTML.

from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from tandem_repeat.application.search import SourceError
from tandem_repeat.infrastructure.html import html_to_text

MAX_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 10


def _decode_text(data: bytes, encoding: str) -> str:
    if len(data) > MAX_BYTES:
        raise SourceError(f"Размер источника превышает {MAX_BYTES} байт.")
    try:
        return data.decode(encoding)
    except (UnicodeError, LookupError) as error:
        raise SourceError(f"Не удалось декодировать текст: {error}") from error


@dataclass(frozen=True)
class StringSource:
    # Источник текста, введенного пользователем.

    text: str

    def read(self) -> str:
        return self.text


@dataclass(frozen=True)
class FileSource:
    # Читает текстовый файл, ограничивая размер до декодирования.

    path: Path
    encoding: str = "utf-8-sig"

    def read(self) -> str:
        try:
            with self.path.open("rb") as stream:
                data = stream.read(MAX_BYTES + 1)
        except OSError as error:
            raise SourceError(f"Не удалось прочитать файл: {error}") from error
        return _decode_text(data, self.encoding)


@dataclass(frozen=True)
class URLSource:
    # Загружает текст по HTTP(S) с ограничением размера и тайм-аутом.

    url: str

    def read(self) -> str:
        try:
            request = _create_request(self.url)
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                media_type = _supported_media_type(response.headers)
                encoding = (
                    response.headers.get_content_charset() or "utf-8-sig"
                )
                data = response.read(MAX_BYTES + 1)
        except (OSError, URLError, ValueError) as error:
            raise SourceError(f"Не удалось загрузить URL: {error}") from error
        text = _decode_text(data, encoding)
        return html_to_text(text) if media_type == "text/html" else text


def _create_request(url: str) -> Request:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Нужен абсолютный URL с http:// или https://.")
    return Request(url, headers={"User-Agent": "TandemRepeatSearch/1.0"})


def _supported_media_type(headers: Message) -> str:
    media_type = headers.get_content_type()
    if media_type not in {"text/html", "text/plain"}:
        raise SourceError(f"Неподдерживаемый тип: {media_type}")
    return media_type
