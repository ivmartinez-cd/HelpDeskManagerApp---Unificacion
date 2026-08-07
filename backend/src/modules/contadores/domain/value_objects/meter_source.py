from dataclasses import dataclass

from src.modules.contadores.domain.errors import InvalidMeterSourceError

_VALID_VALUES = {"sds", "ers"}


@dataclass(frozen=True, slots=True)
class MeterSource:
    """Origen de un contador de impresora: HP SDS o Epson ERS."""

    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_VALUES:
            raise InvalidMeterSourceError(self.value)
