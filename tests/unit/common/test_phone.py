import pytest

from codex_core.common.phone import normalize_phone

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "phone, expected",
    [
        ("+491511234567", "491511234567"),
        ("00491511234567", "491511234567"),
        ("0151 1234567", "491511234567"),
        ("1511234567", "1511234567"),
        (" +49 (151) 123-45-67 ", "491511234567"),
        ("", ""),
        (None, ""),
        ("abc", ""),
    ],
)
def test_normalize_phone(phone, expected):
    assert normalize_phone(phone) == expected


def test_normalize_phone_custom_country():
    # Example: US (+1)
    assert normalize_phone("0123", default_country="1") == "1123"
