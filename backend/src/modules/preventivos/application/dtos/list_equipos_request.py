from dataclasses import dataclass
from typing import Literal

from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)

# Columnas de la tabla de preventivos por las que se puede ordenar.
CampoOrdenEquipos = Literal[
    "cliente",
    "sucursal",
    "equipo",
    "ultimo_preventivo",
    "frecuencia",
    "vencimiento",
    "estado",
    "habilitado",
]


@dataclass(frozen=True, slots=True)
class ListEquiposPorZonaRequest:
    zona: str
    estado: EstadoPreventivo | None = None
    habilitado: bool | None = None
    search: str | None = None
    force_refresh: bool = False
    # None = orden de negocio (vencidos primero, más atrasado arriba).
    orden: CampoOrdenEquipos | None = None
    descendente: bool = False
