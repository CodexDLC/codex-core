import pytest

from codex_core.core.base_dto import BaseDTO
from codex_core.core.pii import is_pii_field, mask_value

pytestmark = pytest.mark.unit


def test_is_pii_field():
    assert is_pii_field("email") is True
    assert is_pii_field("customer_phone") is True
    assert is_pii_field("user_name") is True
    assert is_pii_field("address_info") is True
    assert is_pii_field("comment") is True
    assert is_pii_field("some_other_field") is False


def test_mask_value_recursive():
    # Simple PII
    assert mask_value("email", "test@test.com") == "***"

    # Dictionary with PII
    raw_dict = {"email": "test@test.com", "other": "public"}
    masked_dict = mask_value("user_data", raw_dict)
    assert masked_dict == {"email": "***", "other": "public"}

    # List of dictionaries with PII
    raw_list = [{"phone": "123"}, {"public": "yes"}]
    masked_list = mask_value("items", raw_list)
    assert masked_list == [{"phone": "***"}, {"public": "yes"}]


class UserDTO(BaseDTO):
    email: str
    phone_number: str
    full_name: str
    public_id: int
    extra_data: dict


def test_base_dto_repr_masking():
    dto = UserDTO(
        email="user@test.com",
        phone_number="+491761234567",
        full_name="Ivan Ivanov",
        public_id=123,
        extra_data={"note": "secret stuff", "city": "Berlin"},
    )

    repr_str = repr(dto)

    # Should be masked
    assert "email='***'" in repr_str
    assert "phone_number='***'" in repr_str
    assert "full_name='***'" in repr_str
    assert "'note': '***'" in repr_str

    # Should NOT be masked
    assert "public_id=123" in repr_str
    assert "'city': 'Berlin'" in repr_str
