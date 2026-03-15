"""
codex_tools.common.phone
========================
Universal tools for working with phone numbers.
Framework-agnostic (does not depend on Django).
"""


def normalize_phone(phone: str, default_country: str = "49") -> str:
    """
    Normalizes a phone number by correctly handling +, 00, and local 0.
    Returns only digits.

    Example:
    '0151 1234567' -> '491511234567'
    '+49 151 1234567' -> '491511234567'
    '0049 151 1234567' -> '491511234567'
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
