import pytest

from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    _normalize,
)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Ivan Martinez", "Ivan Martinez"),
        ("Ivan Martinez", "ivan martinez"),
        ("María José Vela", "Maria Jose Vela"),
        ("  Maria   Jose  Vela ", "Maria Jose Vela"),
    ],
)
def test_normalize_matches_case_accent_and_whitespace_variants(a: str, b: str) -> None:
    assert _normalize(a) == _normalize(b)


def test_normalize_does_not_match_different_people() -> None:
    assert _normalize("Ivan Martinez") != _normalize("Ivan Martin")
