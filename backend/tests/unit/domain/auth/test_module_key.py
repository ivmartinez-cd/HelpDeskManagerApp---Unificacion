import pytest

from src.modules.auth.domain.errors import InvalidModuleKeyError
from src.modules.auth.domain.value_objects.module_key import ModuleKey


def test_accepts_a_well_formed_key() -> None:
    ModuleKey("parque-impresoras")


@pytest.mark.parametrize("raw", ["", "A", "1abc", "Insumos", "insumos_x", "a" * 41])
def test_rejects_a_malformed_key(raw: str) -> None:
    with pytest.raises(InvalidModuleKeyError):
        ModuleKey(raw)
