# В тестах видны аргументы запуска, действие и ожидаемый вывод.

import subprocess
import sys
from pathlib import Path

import pytest

from tandem_repeat import __main__ as entry_point
from tandem_repeat.application.search import SearchService, SourceError
from tandem_repeat.domain.tandem import RegexTandemMatcher
from tandem_repeat.infrastructure.sources import URLSource
from tandem_repeat.presentation.console import Console


# Приложение.
@pytest.fixture
def application():
    return Console(SearchService(RegexTandemMatcher()))


# Проверка поиска в тексте.
def test_text_search(capsys):
    code = entry_point.main(["--text", "мама abcabc"])
    output = capsys.readouterr()

    assert code == 0
    assert "Найдено: 2" in output.out
    assert "мама = ма + ма [0:4]" in output.out
    assert output.err == ""


# Проверка отсутствия запроса ввода для пустого текста.
def test_empty_text_does_not_prompt(application, capsys, monkeypatch):
    # Чтение пользовательского ввода.
    def read_input(prompt):
        pytest.fail("Пустой --text не должен запрашивать ввод")

    monkeypatch.setattr("builtins.input", read_input)

    code = application.run(["--text", ""])
    output = capsys.readouterr()

    assert code == 0
    assert output.out == "Найдено: 0\n"
    assert output.err == ""


# Проверка слова, переданного через аргументы запуска.
@pytest.mark.parametrize(
    "word, expected_code, expected_message",
    [
        ("мама", 0, "Тандемный повтор.\n"),
        ("abc", 1, "Не тандемный повтор.\n"),
        ("", 1, "Не тандемный повтор.\n"),
    ],
)
def test_check_from_arguments(
    application, capsys, word, expected_code, expected_message
):
    code = application.run(["--check", word])
    output = capsys.readouterr()

    assert code == expected_code
    assert output.out == expected_message
    assert output.err == ""


# Проверка интерактивного ввода.
def test_interactive_input(application, capsys, monkeypatch):
    # Чтение пользовательского ввода.
    def read_input(prompt):
        return "папа"

    monkeypatch.setattr("builtins.input", read_input)

    code = application.run([])
    output = capsys.readouterr()

    assert code == 0
    assert "папа = па + па" in output.out
    assert output.err == ""


# Проверка ошибки интерактивного ввода.
@pytest.mark.parametrize("error", [EOFError(), KeyboardInterrupt()])
def test_interactive_failure(application, capsys, monkeypatch, error):
    # Чтение пользовательского ввода.
    def read_input(prompt):
        raise error

    monkeypatch.setattr("builtins.input", read_input)

    code = application.run([])
    output = capsys.readouterr()

    assert code == 2
    assert output.out == ""
    assert "Ошибка ввода" in output.err


# Проверка ввода из файла и выбора кодировки.
def test_file_input_and_encoding(application, capsys, tmp_path):
    path = tmp_path / "input.txt"
    path.write_bytes("мама".encode("cp1251"))

    code = application.run(["--file", str(path), "--encoding", "cp1251"])
    output = capsys.readouterr()

    assert code == 0
    assert "мама = ма + ма" in output.out
    assert output.err == ""


# Проверка ввода по URL.
def test_url_input(application, capsys, monkeypatch):
    # Чтение страницы.
    def read_page(source):
        assert source.url == "https://example.org"
        return "abcabc"

    monkeypatch.setattr(URLSource, "read", read_page)

    code = application.run(["--url", "https://example.org"])
    output = capsys.readouterr()

    assert code == 0
    assert "abcabc = abc + abc" in output.out
    assert output.err == ""


# Проверка ошибки источника.
def test_source_error(application, capsys, monkeypatch):
    # Чтение страницы.
    def read_page(source):
        raise SourceError("offline")

    monkeypatch.setattr(URLSource, "read", read_page)

    code = application.run(["--url", "https://example.org"])
    output = capsys.readouterr()

    assert code == 2
    assert output.out == ""
    assert "offline" in output.err


# Проверка взаимоисключающих аргументов источников.
def test_sources_are_mutually_exclusive(application):
    with pytest.raises(SystemExit) as error:
        application.run(["--text", "aa", "--check", "aa"])

    assert error.value.code == 2


# Проверка успешного завершения после вывода справки.
def test_help_exits_successfully(application, capsys):
    with pytest.raises(SystemExit) as error:
        application.run(["--help"])

    assert error.value.code == 0
    assert "--check" in capsys.readouterr().out


# Проверка запуска программы как модуля.
def test_module_launch():
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "tandem_repeat", "--check", "aa"],
        capture_output=True,
        text=True,
        cwd=project_root,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == "Тандемный повтор.\n"


# Проверка запуска файла из другой папки.
def test_file_launch_from_another_directory(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "tandem_repeat" / "__main__.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        input="мама\n",
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Найдено: 1" in result.stdout
    assert "мама = ма + ма [0:4]" in result.stdout
