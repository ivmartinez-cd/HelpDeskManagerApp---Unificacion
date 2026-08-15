import pytest

from src.shared.domain.errors import InvalidModuleKeyError
from src.shared.domain.value_objects.module_key import ModuleKey


def test_accepts_a_well_formed_key() -> None:
    ModuleKey("analisis-log-hp")


@pytest.mark.parametrize("raw", ["", "A", "1abc", "Insumos", "insumos_x", "a" * 41])
def test_rejects_a_malformed_key(raw: str) -> None:
    with pytest.raises(InvalidModuleKeyError):
        ModuleKey(raw)
