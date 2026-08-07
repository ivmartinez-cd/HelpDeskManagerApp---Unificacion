import pytest

from src.shared.domain.errors import InvalidActionKeyError
from src.shared.domain.value_objects.action_key import ActionKey


def test_accepts_a_well_formed_key() -> None:
    ActionKey("approve")


@pytest.mark.parametrize("raw", ["", "A", "1abc", "Approve", "approve!"])
def test_rejects_a_malformed_key(raw: str) -> None:
    with pytest.raises(InvalidActionKeyError):
        ActionKey(raw)
