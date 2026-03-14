"""
codex_tools.common.phone
========================
Universal tools for working with phone numbers.
Framework-agnostic (does not depend on Django).
"""


def normalize_phone(phone: str) -> str:
    """
    Brings a phone number to a canonical format: only digits, no plus sign.

    Logic:
    1. Keep only digits.
    2. If it starts with '0' (German local format), replace '0' with '49'.
    3. Otherwise, return only digits (assuming the country code is already present).

    Example:
    '0151 1234567' -> '491511234567'
    '+49 151 1234567' -> '491511234567'
    """
    if not phone:
        return ""

    # 1. Only digits
    digits = "".join(filter(str.isdigit, phone))

    if not digits:
        return ""

    # 2. Handle local German format (0...)
    if digits.startswith("0") and len(digits) >= 10:
        return "49" + digits[1:]

    # 3. Return as is (assuming international format)
    return digits
