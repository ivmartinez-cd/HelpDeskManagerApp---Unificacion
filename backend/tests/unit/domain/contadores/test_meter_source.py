import pytest

from src.modules.contadores.domain.errors import InvalidMeterSourceError
from src.modules.contadores.domain.value_objects.meter_source import MeterSource


@pytest.mark.parametrize("raw", ["sds", "ers"])
def test_accepts_known_sources(raw: str) -> None:
    MeterSource(raw)


@pytest.mark.parametrize("raw", ["", "SDS", "epson", "hp"])
def test_rejects_unknown_sources(raw: str) -> None:
    with pytest.raises(InvalidMeterSourceError):
        MeterSource(raw)
