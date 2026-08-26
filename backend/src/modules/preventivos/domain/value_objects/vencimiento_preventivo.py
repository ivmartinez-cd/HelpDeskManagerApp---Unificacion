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
    inventada (regla de negocio del módulo).

    `fecha_tentativa` es la única excepción parcial a esa regla: cuando el
    equipo está `sin_preventivo` pero hubo una Instalación-Desinstalación
    real y con frecuencia cargada, es "instalación + frecuencia" — no
    reemplaza `proximo_vencimiento` (el estado sigue siendo `sin_preventivo`,
    nunca al_dia/vencido a partir de una instalación), es solo una referencia
    informativa de cuándo correspondería el primer preventivo."""

    estado: EstadoPreventivo
    proximo_vencimiento: date | None
    dias_vencido: int | None
    fecha_tentativa: date | None = None
