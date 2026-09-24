"""Cambio de estado de un envío que el job observó en OCA (tabla
`insumos_despacho_estado_historial`). No es la historia completa de OCA:
`GetEnvioEstadoActual` solo devuelve el estado actual."""

from dataclasses import dataclass
from datetime import date, datetime

from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo


@dataclass(frozen=True, slots=True)
class CambioEstado:
    id_estado: int | None
    estado: str
    motivo: str
    sucursal: str
    fecha_estado: date
    color: ColorSemaforo
    """Color que tenía el envío con ese estado."""
    observado_en: datetime
