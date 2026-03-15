"""Text processing utilities for name normalization, transliteration, and SMS safety.

Framework-agnostic (zero Django / framework dependencies).  All
functions are pure and stateless: they accept a string, return a
string, and produce no side effects.

Functions are organized around three distinct concerns:

- **Normalization** — :func:`normalize_name`, :func:`clean_string`
  produce canonical, whitespace-clean representations.
- **Transliteration** — :func:`transliterate` converts Cyrillic to
  Latin for systems that do not support Unicode input.
- **Sanitization** — :func:`sanitize_for_sms` strips characters
  illegal or problematic in SMS payloads.
"""

import re


def normalize_name(name: str) -> str:
    """Capitalize each word in a personal name, preserving hyphens.

    Collapses repeated whitespace, then title-cases every name
    segment separated by a space or hyphen while leaving the
    delimiters unchanged.

    Args:
        name: Raw name string in any case with arbitrary spacing
            (e.g. ``"  ivan   ivanov-petrov  "``).

    Returns:
        Normalized name with each segment capitalized
        (e.g. ``"Ivan Ivanov-Petrov"``), or an empty string if
        *name* is falsy.

    Example:
        ```python
        normalize_name("ivan ivanov-petrov")  # → "Ivan Ivanov-Petrov"
        normalize_name("ANNA MÜLLER")          # → "Anna Müller"
        normalize_name("")                     # → ""
        ```
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
    """Collapse multiple whitespace characters into a single space.

    Strips leading / trailing whitespace and replaces any internal
    sequence of whitespace (spaces, tabs, newlines) with a single
    ASCII space.  Invisible Unicode whitespace is also collapsed
    because ``str.split()`` is Unicode-aware.

    Args:
        text: Raw string that may contain irregular whitespace.

    Returns:
        Cleaned string with normalized whitespace, or an empty string
        if *text* is falsy.

    Example:
        ```python
        clean_string("  hello\\t  world\\n")  # → "hello world"
        clean_string("")                       # → ""
        ```
    """
    if not text:
        return ""
    return " ".join(text.split())


def transliterate(text: str) -> str:
    """Transliterate Cyrillic characters to their Latin equivalents.

    Uses a hard-coded character-level mapping (``str.maketrans``)
    covering all 33 letters of the Russian alphabet in both cases.
    Non-Cyrillic characters pass through unchanged.

    The mapping follows a simplified scientific transliteration
    standard (not GOST 7.79-2000) optimised for readability in
    Latin-script contexts such as SMS gateways and URL slugs.

    Args:
        text: Input string containing Cyrillic characters.

    Returns:
        String with each Cyrillic character replaced by its Latin
        approximation, or an empty string if *text* is falsy.

    Note:
        ``ъ`` (hard sign) and ``ь`` (soft sign) map to an empty
        string, reducing the output length relative to the input.

    Example:
        ```python
        transliterate("Привет")        # → "Privet"
        transliterate("Щукин")         # → "Shchukin"
        transliterate("Hello World")   # → "Hello World"  (passthrough)
        ```
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
    """Produce a safe, length-bounded string suitable for SMS payloads.

    Applies two successive regex passes:

    1. Replaces ``\\r``, ``\\n``, ``\\t`` sequences with a single space
       to eliminate line breaks that most SMS gateways convert to
       encoding errors.
    2. Strips all characters outside the set ``[\\w\\s.\\-]``
       (word characters, spaces, dots, hyphens).

    The result is then truncated to *max_length* characters and
    stripped of trailing whitespace.

    Args:
        text: Arbitrary user-supplied or templated string.
        max_length: Maximum number of characters in the output.
            Defaults to ``50``, which fits within a single GSM-7
            SMS segment alongside typical prefix text.

    Returns:
        Sanitized and truncated string, or an empty string if *text*
        is falsy.

    Note:
        Truncation happens *before* the final ``strip()``, so the
        effective output length may be slightly less than *max_length*
        when the truncation boundary falls on whitespace.

    Example:
        ```python
        sanitize_for_sms("Hello\\nWorld!!! <script>", 20)
        # → "Hello World script"

        sanitize_for_sms("Appointment at 10:00", 15)
        # → "Appointment at"
        ```
    """
    if not text:
        return ""
    # Remove newlines and control characters
    clean = re.sub(r"[\r\n\t]+", " ", text)
    # Keep only safe characters: word chars, spaces, dots, dashes
    clean = re.sub(r"[^\w\s.\-]", "", clean)
    return clean[:max_length].strip()
