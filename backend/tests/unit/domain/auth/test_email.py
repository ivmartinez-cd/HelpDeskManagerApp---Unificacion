import pytest

from src.modules.auth.domain.errors import InvalidEmailError
from src.modules.auth.domain.value_objects.email import Email


def test_normalizes_to_lowercase() -> None:
    email = Email("  Admin@Example.COM ")

    assert email.value == "admin@example.com"


@pytest.mark.parametrize("raw", ["not-an-email", "missing-domain@", "@no-local-part.com", ""])
def test_rejects_invalid_format(raw: str) -> None:
    with pytest.raises(InvalidEmailError):
        Email(raw)
