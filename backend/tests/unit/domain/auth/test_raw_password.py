import pytest

from src.modules.auth.domain.errors import WeakPasswordError
from src.modules.auth.domain.value_objects.raw_password import RawPassword


def test_accepts_a_password_meeting_all_rules() -> None:
    RawPassword("ValidPass123!")


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        ("Ab1!", "al menos 8 caracteres"),
        ("lowercase1!", "mayúscula"),
        ("NoDigitsHere!", "número"),
        ("NoSpecial123", "carácter especial"),
    ],
)
def test_rejects_a_password_missing_one_rule(raw: str, reason: str) -> None:
    with pytest.raises(WeakPasswordError, match=reason):
        RawPassword(raw)
