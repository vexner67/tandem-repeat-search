# Файлы создаются во временной папке, HTTP-ответ заменяется потоком байт.

from email.message import Message
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from tandem_repeat.application.search import SourceError
from tandem_repeat.domain.tandem import RegexTandemMatcher
from tandem_repeat.infrastructure import sources
from tandem_repeat.infrastructure.html import html_to_text
from tandem_repeat.infrastructure.sources import (
    FileSource,
    URLSource,
)


# Создание ответа.
def make_response(data, content_type):
    # Готовый поток байт поддерживает read и with без отдельного класса.
    response = BytesIO(data)
    response.headers = Message()
    response.headers["Content-Type"] = content_type
    return response


# Предоставление ответа.
def provide_response(monkeypatch, response):
    # Открытие страницы.
    def open_page(request, timeout):
        return response

    monkeypatch.setattr(sources, "urlopen", open_page)


# Проверка чтения файла в выбранной кодировке.
@pytest.mark.parametrize("encoding", ["utf-8-sig", "cp1251"])
def test_file_reads_selected_encoding(tmp_path, encoding):
    path = tmp_path / "text.txt"
    path.write_bytes("мама".encode(encoding))

    assert FileSource(path, encoding).read() == "мама"


# Проверка чтения UTF-8 с BOM в кодировке по умолчанию.
def test_default_encoding_reads_utf8_bom(tmp_path):
    path = tmp_path / "text.txt"
    path.write_bytes("мама".encode("utf-8-sig"))

    assert FileSource(path).read() == "мама"


# Проверка пустого файла.
def test_empty_file(tmp_path):
    path = tmp_path / "text.txt"
    path.write_bytes(b"")

    assert FileSource(path).read() == ""


# Проверка отсутствующего файла.
def test_missing_file(tmp_path):
    with pytest.raises(SourceError, match="прочитать файл"):
        FileSource(tmp_path / "missing.txt").read()


# Проверка некорректной кодировки файла.
@pytest.mark.parametrize("encoding", ["utf-8", "nonexistent-encoding"])
def test_invalid_file_encoding(tmp_path, encoding):
    path = tmp_path / "text.txt"
    path.write_bytes(b"\xff")

    with pytest.raises(SourceError, match="декодировать"):
        FileSource(path, encoding).read()


# Проверка ограничения размера файла.
def test_file_size_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "MAX_BYTES", 4)
    path = tmp_path / "text.txt"
    path.write_bytes(b"aaaaa")

    with pytest.raises(SourceError, match="Размер"):
        FileSource(path).read()

    path.write_bytes(b"aaaa")

    assert FileSource(path).read() == "aaaa"


# Проверка извлечения текста и HTML-ссылок на символы.
def test_html_extracts_text_and_entities():
    markup = '<p title="папа">мама &amp; abcabc</p>'

    assert html_to_text(markup) == " мама & abcabc "


# Проверка пропуска скрытого содержимого, атрибутов и комментариев HTML.
def test_html_ignores_hidden_content_attributes_and_comments():
    markup = (
        "<script>мама</script><style>папа</style>"
        "<noscript>aa</noscript><template><b>bb</b></template>"
        '<!-- abcabc --><img alt="zz">видимый'
    )

    assert html_to_text(markup).strip() == "видимый"


# Проверка отсутствия склеивания слов между блоками HTML.
def test_html_blocks_do_not_join_words():
    text = html_to_text("<p>ма</p><p>ма</p>ма<br>ма")
    matcher = RegexTandemMatcher()

    assert matcher.find_tandems(text) == []


# Проверка сохранения слова внутри строчных тегов HTML.
def test_html_inline_tags_preserve_word():
    assert html_to_text("ма<b>ма</b>") == "мама"


# Проверка вложенных тегов скрытого содержимого HTML.
def test_html_nested_hidden_tags():
    markup = "<template><template>aa</template>bb</template>cc"

    assert html_to_text(markup) == "  cc"


# Проверка самозакрывающихся тегов HTML.
@pytest.mark.parametrize(
    "markup, expected",
    [
        ("ма<br/>ма", "ма ма"),
        ("<script/>мама<b/>!", " мама!"),
        ("<template><br/>aa</template>папа", " папа"),
    ],
)
def test_html_self_closing_tags(markup, expected):
    assert html_to_text(markup) == expected


# Проверка загрузки HTML по URL с тайм-аутом и ограничением размера.
def test_url_loads_html_with_timeout_and_size_limit(monkeypatch):
    response = make_response(b"<p>abcabc</p>", "text/html; charset=utf-8")
    requests = []
    read_sizes = []

    # Открытие страницы.
    def open_page(request, timeout):
        requests.append((request.full_url, timeout))
        return response

    # Чтение страницы.
    def read_page(size):
        read_sizes.append(size)
        return b"<p>abcabc</p>"

    monkeypatch.setattr(sources, "urlopen", open_page)
    monkeypatch.setattr(response, "read", read_page)

    text = URLSource("https://example.org").read()

    assert text == " abcabc "
    assert requests == [("https://example.org", 10)]
    assert read_sizes == [5 * 1024 * 1024 + 1]
    assert response.closed


# Проверка чтения URL в указанной кодировке или кодировке по умолчанию.
@pytest.mark.parametrize(
    "content_type, data",
    [
        ("text/plain; charset=windows-1251", "папа".encode("cp1251")),
        ("text/plain", "папа".encode("utf-8-sig")),
    ],
)
def test_url_reads_declared_or_default_encoding(
    monkeypatch, content_type, data
):
    response = make_response(data, content_type)
    provide_response(monkeypatch, response)

    assert URLSource("http://example.org").read() == "папа"
    assert response.closed


# Проверка отсутствия запроса при некорректном URL.
@pytest.mark.parametrize(
    "url",
    [
        "",
        "example.org",
        "ftp://example.org",
        "https:///a",
        "file:///etc/passwd",
        "http://[invalid",
    ],
)
def test_invalid_url_does_not_send_request(monkeypatch, url):
    # Открытие страницы.
    def open_page(request, timeout):
        pytest.fail("Некорректный URL не должен вызывать загрузку")

    monkeypatch.setattr(sources, "urlopen", open_page)

    with pytest.raises(SourceError):
        URLSource(url).read()


# Проверка отклонения двоичного содержимого URL без чтения.
def test_url_rejects_binary_content_without_reading(monkeypatch):
    response = make_response(b"image", "image/png")
    provide_response(monkeypatch, response)

    # Чтение страницы.
    def read_page(size):
        pytest.fail("Неподдерживаемое содержимое не должно читаться")

    monkeypatch.setattr(response, "read", read_page)

    with pytest.raises(SourceError, match="тип"):
        URLSource("https://example.org").read()

    assert response.closed


# Проверка сообщения о сетевой ошибке при загрузке URL.
@pytest.mark.parametrize(
    "error",
    [
        URLError("offline"),
        TimeoutError("timeout"),
        HTTPError("https://example.org", 404, "Missing", None, None),
        ValueError("bad request"),
    ],
)
def test_url_explains_network_failure(monkeypatch, error):
    # Открытие страницы.
    def open_page(request, timeout):
        raise error

    monkeypatch.setattr(sources, "urlopen", open_page)

    with pytest.raises(SourceError, match="загрузить URL"):
        URLSource("https://example.org").read()


# Проверка ограничения размера ответа по URL.
def test_url_size_limit(monkeypatch):
    monkeypatch.setattr(sources, "MAX_BYTES", 4)
    response = make_response(b"aaaaa", "text/plain")
    provide_response(monkeypatch, response)

    with pytest.raises(SourceError, match="Размер"):
        URLSource("https://example.org").read()

    assert response.closed


# Проверка сообщения о некорректной кодировке ответа по URL.
@pytest.mark.parametrize(
    "content_type, data",
    [
        ("text/plain; charset=absent", b"aa"),
        ("text/plain; charset=utf-8", b"\xff"),
    ],
)
def test_url_explains_invalid_encoding(monkeypatch, content_type, data):
    response = make_response(data, content_type)
    provide_response(monkeypatch, response)

    with pytest.raises(SourceError, match="декодировать"):
        URLSource("https://example.org").read()
