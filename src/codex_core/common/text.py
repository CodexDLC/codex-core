"""
codex_core.common.text
=======================
Universal tools for working with text.
Framework-agnostic (does not depend on Django).
"""

import re


def normalize_name(name: str) -> str:
    """
    Brings first/last name to a standard form, preserving spaces and hyphens.
    Example: 'ivan ivanov-petrov' -> 'Ivan Ivanov-Petrov'
    """
    if not name:
        return ""

    # Normalize spaces (remove extra ones)
    cleaned_name = " ".join(name.strip().split())

    # Split by spaces OR hyphens, PRESERVING the delimiters
    parts = re.split(r"([\s-])", cleaned_name)

    # Capitalize only text parts, leave delimiters as is
    normalized_parts = [p.capitalize() if p not in (" ", "-") else p for p in parts]

    return "".join(normalized_parts)


def clean_string(text: str) -> str:
    """Removes extra spaces and invisible characters."""
    if not text:
        return ""
    return " ".join(text.split())


def transliterate(text: str) -> str:
    """
    Transliterate Cyrillic characters to Latin equivalents.

    Example::

        transliterate("Привет")  # → "Privet"
    """
    if not text:
        return ""

    translit_map = str.maketrans(
        {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "yo",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "kh",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "shch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
            "А": "A",
            "Б": "B",
            "В": "V",
            "Г": "G",
            "Д": "D",
            "Е": "E",
            "Ё": "Yo",
            "Ж": "Zh",
            "З": "Z",
            "И": "I",
            "Й": "Y",
            "К": "K",
            "Л": "L",
            "М": "M",
            "Н": "N",
            "О": "O",
            "П": "P",
            "Р": "R",
            "С": "S",
            "Т": "T",
            "У": "U",
            "Ф": "F",
            "Х": "Kh",
            "Ц": "Ts",
            "Ч": "Ch",
            "Ш": "Sh",
            "Щ": "Shch",
            "Ъ": "",
            "Ы": "Y",
            "Ь": "",
            "Э": "E",
            "Ю": "Yu",
            "Я": "Ya",
        }
    )
    return text.translate(translit_map)


def sanitize_for_sms(text: str, max_length: int = 50) -> str:
    """
    Clean string for safe SMS sending.

    Removes newlines, control characters, and non-safe symbols.
    Truncates to ``max_length`` (default: 50).

    Example::

        sanitize_for_sms("Hello\\nWorld!!! <script>", 20)  # → "Hello World script"
    """
    if not text:
        return ""
    # Remove newlines and control characters
    clean = re.sub(r"[\r\n\t]+", " ", text)
    # Keep only safe characters: word chars, spaces, dots, dashes
    clean = re.sub(r"[^\w\s.\-]", "", clean)
    return clean[:max_length].strip()
