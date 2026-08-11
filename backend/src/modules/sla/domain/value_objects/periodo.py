import calendar
from dataclasses import dataclass
from datetime import date

from src.modules.sla.domain.errors import PeriodoInvalidoError

# Siges tiene incidentes desde mucho antes, pero un período fuera de este rango
# es casi seguro un typo del selector (ej. 20268 en vez de 202608).
_ANIO_MIN = 2000
_ANIO_MAX = 2100


@dataclass(frozen=True, slots=True)
class Periodo:
    """Período mensual AAAAMM (ej. 202608) — el mismo formato que la columna
    calculada `Periodo` de la consulta a Siges. El rango Desde/Hasta de la
    consulta se deriva de acá (primer/último día del mes), no se pide aparte."""

    value: int

    def __post_init__(self) -> None:
        if not (_ANIO_MIN <= self.anio <= _ANIO_MAX and 1 <= self.mes <= 12):
            raise PeriodoInvalidoError(self.value)

    @property
    def anio(self) -> int:
        return self.value // 100

    @property
    def mes(self) -> int:
        return self.value % 100

    @property
    def primer_dia(self) -> date:
        return date(self.anio, self.mes, 1)

    @property
    def ultimo_dia(self) -> date:
        return date(self.anio, self.mes, calendar.monthrange(self.anio, self.mes)[1])
