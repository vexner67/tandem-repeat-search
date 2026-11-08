# Извлечение текста из статической HTML-разметки.

from html.parser import HTMLParser


def html_to_text(html: str) -> str:
    # Извлекает статический текст без выполнения JavaScript и CSS.
    parser = _HTMLTextParser()
    parser.feed(html)
    parser.close()
    return "".join(parser.parts)


class _HTMLTextParser(HTMLParser):
    # Сохраняет слова внутри строчных тегов и разделяет блочные элементы.

    _hidden = {"script", "style", "noscript", "template"}
    _blocks = set(
        "address article aside blockquote br div dl dt dd footer form "
        "h1 h2 h3 h4 h5 h6 header hr li main nav ol p pre section "
        "table td th tr ul".split()
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_tags: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in self._hidden:
            self.hidden_tags.append(tag)
            self.parts.append(" ")
        elif tag in self._blocks and not self.hidden_tags:
            self.parts.append(" ")

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        # Самозакрывающийся тег не открывает область скрытого содержимого.
        if not self.hidden_tags and tag in self._hidden | self._blocks:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if self.hidden_tags:
            if tag == self.hidden_tags[-1]:
                self.hidden_tags.pop()
        elif tag in self._blocks:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden_tags:
            self.parts.append(data)
