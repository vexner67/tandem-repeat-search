# Правила проверяются на примерах и независимым сравнением половин.

from itertools import product

import pytest

from tandem_repeat.domain.tandem import RegexTandemMatcher, TandemMatch


# Проверка принятия слов с одинаковыми непустыми половинами.
@pytest.mark.parametrize(
    "word",
    [
        "aa",
        "мама",
        "папа",
        "abcabc",
        "ATGCATGC",
        "aaaa",
        "abababab",
        "ЁжЁж",
        "ёё",
        "АБАБ",
        "AaAa",
        "аbаb",
        "zzzzzz",
    ],
)
def test_accepts_equal_nonempty_halves(word):
    matcher = RegexTandemMatcher()

    assert matcher.is_tandem(word)


# Проверка отклонения некорректных слов.
@pytest.mark.parametrize(
    "word",
    [
        "",
        "a",
        "aaa",
        "abcab",
        "abcabcabc",
        "ATGCATGCATGC",
        "Мама",
        "aA",
        " мама",
        "мама ",
        "мама\n",
        "ма ма",
        "ма-ма",
        "1212",
        "aa1",
        "aa_",
        "éé",
        "漢漢",
        "🙂🙂",
        "aа",
        "маМa",
    ],
)
def test_rejects_invalid_words(word):
    matcher = RegexTandemMatcher()

    assert not matcher.is_tandem(word)


# Сравнение результатов для коротких слов с независимой проверкой.
def test_short_words_match_independent_check():
    matcher = RegexTandemMatcher()

    # Перебираем все слова длиной до восьми из трех выбранных букв.
    for length in range(9):
        for symbols in product("abА", repeat=length):
            word = "".join(symbols)
            middle = length // 2
            expected = (
                length > 0
                and length % 2 == 0
                and word[:middle] == word[middle:]
            )

            assert matcher.is_tandem(word) == expected, word


# Проверка сохранения слов, половин, координат и повторных вхождений.
def test_search_preserves_words_halves_offsets_and_duplicates():
    matcher = RegexTandemMatcher()
    text = "🙂 мама, abcabc! мама"

    matches = matcher.find_tandems(text)

    assert matches == [
        TandemMatch("мама", "ма", 2, 6),
        TandemMatch("abcabc", "abc", 8, 14),
        TandemMatch("мама", "ма", 16, 20),
    ]


# Проверка отсутствия частичных совпадений внутри токена.
def test_search_does_not_extract_part_of_a_token():
    matcher = RegexTandemMatcher()
    text = "xмама мамах 1мама мама1 _мама мама_ éмама мама漢"

    assert matcher.find_tandems(text) == []


# Проверка разделения слов пунктуацией и переводами строк.
def test_punctuation_and_line_breaks_separate_words():
    matcher = RegexTandemMatcher()
    text = "(мама);папа\nabcabc—aa-ма-ма"

    matches = matcher.find_tandems(text)

    assert [match.word for match in matches] == [
        "мама",
        "папа",
        "abcabc",
        "aa",
    ]


# Проверка поиска без совпадений.
@pytest.mark.parametrize("text", ["", "обычный текст"])
def test_search_without_matches(text):
    matcher = RegexTandemMatcher()

    assert matcher.find_tandems(text) == []


# Проверка целого слова с более чем двумя повторениями.
def test_full_word_can_have_more_than_two_repetitions():
    matcher = RegexTandemMatcher()

    assert matcher.find_tandems("aaaa ababаб abababab") == [
        TandemMatch("aaaa", "aa", 0, 4),
        TandemMatch("abababab", "abab", 12, 20),
    ]
