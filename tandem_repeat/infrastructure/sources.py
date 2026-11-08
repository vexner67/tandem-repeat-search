# Чтение источников с ограничением размера и извлечение текста HTML.

from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from tandem_repeat.application.search import Source, SourceError
from tandem_repeat.infrastructure.html import html_to_text

MAX_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class StringSource(Source):
    # Источник текста, введенного пользователем.

    text: str

    def read(self) -> str:
        return self.text


@dataclass(frozen=True)
class FileSource(Source):
    # Читает текстовый файл, ограничивая размер до декодирования.

    path: Path
    encoding: str = "utf-8-sig"

    def read(self) -> str:
        data = self._read_bytes()
        return _decode_text(data, self.encoding)

    def _read_bytes(self) -> bytes:
        try:
            with self.path.open("rb") as stream:
                return stream.read(MAX_BYTES + 1)
        except OSError as error:
            raise SourceError(f"Не удалось прочитать файл: {error}") from error


@dataclass(frozen=True)
class URLSource(Source):
    # Загружает текст по HTTP(S) с ограничением размера и тайм-аутом.

    url: str

    def read(self) -> str:
        data, encoding, media_type = self._download()
        text = _decode_text(data, encoding)
        return html_to_text(text) if media_type == "text/html" else text

    def _download(self) -> tuple[bytes, str, str]:
        # Возвращает байты, кодировку и MIME-тип ответа.
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
        return data, encoding, media_type


def _decode_text(data: bytes, encoding: str) -> str:
    if len(data) > MAX_BYTES:
        raise SourceError(f"Размер источника превышает {MAX_BYTES} байт.")
    try:
        return data.decode(encoding)
    except (UnicodeError, LookupError) as error:
        raise SourceError(f"Не удалось декодировать текст: {error}") from error


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
