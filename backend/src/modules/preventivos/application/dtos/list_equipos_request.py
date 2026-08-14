from dataclasses import dataclass

from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)


@dataclass(frozen=True, slots=True)
class ListEquiposPorZonaRequest:
    zona: str
    estado: EstadoPreventivo | None = None
    habilitado: bool | None = None
    search: str | None = None
    force_refresh: bool = False
