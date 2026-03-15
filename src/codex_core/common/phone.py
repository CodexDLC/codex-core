"""Utilities for normalizing phone numbers to a canonical digit-only format.

Framework-agnostic (zero Django / framework dependencies).  Suitable
for use in any Python 3.10+ environment including async workers.

The module intentionally does not validate that the resulting number is
reachable (no libphonenumber dependency); it only ensures a consistent
digit-only representation that can be safely stored, compared, and
passed to SMS / telephony APIs.
"""


def normalize_phone(phone: str, default_country: str = "49") -> str:
    """Normalize a phone number to a digit-only international string.

    Handles the three most common input variants encountered in
    European / German-locale data:

    1. **International ``+`` prefix** — ``+49 151 1234567``
    2. **International ``00`` prefix** — ``0049 151 1234567``
    3. **Local ``0`` prefix** — ``0151 1234567`` (expanded using
       *default_country*)
    4. **Already normalized** — ``491511234567`` (returned as-is)

    Non-digit, non-plus characters (spaces, hyphens, parentheses) are
    stripped before prefix detection.

    Args:
        phone: Raw phone string in any common format.  Empty string or
            strings containing no digits/plus return ``""``.
        default_country: ITU-T country code (digits only, no ``+``)
            prepended when a local ``0``-prefix number is detected.
            Defaults to ``"49"`` (Germany).

    Returns:
        Digit-only string representing the international phone number,
        or an empty string if the input is blank or contains no
        recognizable digits.

    Note:
        No length or reachability validation is performed.  The caller
        is responsible for validating that the result conforms to the
        expected E.164 length for the target country.

    Example:
        ```python
        normalize_phone("0151 1234567")          # → "491511234567"
        normalize_phone("+49 151 1234567")        # → "491511234567"
        normalize_phone("0049 151 1234567")       # → "491511234567"
        normalize_phone("+1-800-555-0100", "1")   # → "18005550100"
        normalize_phone("")                        # → ""
        ```
    """
    if not phone:
        return ""

    # Keep only digits and plus (if present at start)
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if not cleaned:
        return ""

    # 1. Already has '+' -> remove it and return
    if cleaned.startswith("+"):
        return cleaned.replace("+", "")

    # 2. Starts with '00' (European international format)
    if cleaned.startswith("00"):
        return cleaned[2:]

    # 3. Starts with a single '0' (local format, e.g. German)
    if cleaned.startswith("0"):
        return default_country + cleaned[1:]

    # 4. Already normalized number without plus (e.g. 49151...)
    return cleaned
