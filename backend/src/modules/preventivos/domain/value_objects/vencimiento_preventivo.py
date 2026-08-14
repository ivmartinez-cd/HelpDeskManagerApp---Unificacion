from dataclasses import dataclass
from datetime import date
from typing import Literal

EstadoPreventivo = Literal[
    "vencido", "por_vencer", "al_dia", "sin_preventivo", "sin_frecuencia"
]

ESTADOS_PREVENTIVO: tuple[EstadoPreventivo, ...] = (
    "vencido",
    "por_vencer",
    "al_dia",
    "sin_preventivo",
    "sin_frecuencia",
)


@dataclass(frozen=True, slots=True)
class VencimientoPreventivo:
    """Resultado del cálculo puro de vencimiento. `proximo_vencimiento` y
    `dias_vencido` solo existen cuando hay datos reales para calcularlos —
    "sin_preventivo"/"sin_frecuencia" son estados explícitos, nunca una fecha
    inventada (regla de negocio del módulo)."""

    estado: EstadoPreventivo
    proximo_vencimiento: date | None
    dias_vencido: int | None
