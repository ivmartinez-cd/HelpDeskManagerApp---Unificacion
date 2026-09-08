from dataclasses import dataclass

from src.modules.tareas_varias.domain.errors import PeriodoInvalidoError

# Siges tiene incidentes desde mucho antes, pero un período fuera de este rango
# es casi seguro un typo del selector (ej. 20268 en vez de 202608).
_ANIO_MIN = 2000
_ANIO_MAX = 2100


@dataclass(frozen=True, slots=True)
class Periodo:
    """Período mensual AAAAMM (ej. 202605). Duplicado del homónimo en
    `bono_tecnicos.domain.value_objects.periodo` (sin `periodos_del_anio`,
    que solo usa la evolución anual de gerencia) — mismo criterio que
    `TecnicoNoVinculadoError`, cada módulo con sus propios tipos de dominio."""

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
