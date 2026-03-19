import pytest

from codex_core.common.text import clean_string, normalize_name, sanitize_for_sms, transliterate

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "name, expected",
    [
        ("иван", "Иван"),
        ("ИВАН", "Иван"),
        ("иван иванов-петров", "Иван Иванов-Петров"),
        ("  ANNA-MARIA  ", "Anna-Maria"),
        ("jean-luc picard", "Jean-Luc Picard"),
        (" mCDonald ", "Mcdonald"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_name(name, expected):
    assert normalize_name(name) == expected


def test_clean_string():
    assert clean_string("  hello \n world  ") == "hello world"
    assert clean_string("") == ""
    assert clean_string(None) == ""


def test_transliterate():
    assert transliterate("Привет") == "Privet"
    assert transliterate("Яблоко") == "Yabloko"
    assert transliterate("") == ""
    assert transliterate(None) == ""


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello\nWorld!!! <script>", "Hello World script"),
        (
            "Very long message that should be truncated by default length",
            "Very long message that should be truncated by defa",
        ),
        ("", ""),
        (None, ""),
    ],
)
def test_sanitize_for_sms(text, expected):
    assert sanitize_for_sms(text) == expected
