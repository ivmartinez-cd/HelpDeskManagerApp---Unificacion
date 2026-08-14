from dataclasses import dataclass
from datetime import date, datetime

from src.modules.preventivos.domain.entities.equipo_preventivo import EquipoPreventivo
from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
)


@dataclass(frozen=True, slots=True)
class HabilitacionInfo:
    """Lo que la UI muestra de una habilitación activa (auditoría incluida)."""

    habilitado_por: str
    habilitado_en: datetime
    nota: str | None


@dataclass(frozen=True, slots=True)
class EquipoPreventivoAnotado:
    equipo: EquipoPreventivo
    estado: EstadoPreventivo
    proximo_vencimiento: date | None
    dias_vencido: int | None
    habilitacion: HabilitacionInfo | None


@dataclass(frozen=True, slots=True)
class ListEquiposResult:
    equipos: list[EquipoPreventivoAnotado]
    consultado_en: datetime
