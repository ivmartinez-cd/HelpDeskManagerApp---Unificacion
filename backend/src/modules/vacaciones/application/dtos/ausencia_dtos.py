import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud


@dataclass(frozen=True, slots=True)
class CrearAusenciaCommand:
    """`empleado_ids` vacío = la propia (empleado); jefe/admin pueden alta
    masiva (paridad legacy: sin chequeo de sector en la masiva)."""

    empleado_ids: list[uuid.UUID]
    start_date: date
    end_date: date
    tipo: TipoAusencia
    reason: str | None
    half_day: bool


@dataclass(frozen=True, slots=True)
class EditarAusenciaCommand:
    start_date: date
    end_date: date
    tipo: TipoAusencia
    reason: str | None
    half_day: bool
    status: EstadoSolicitud | None


@dataclass(frozen=True, slots=True)
class ListarAusenciasQuery:
    status: EstadoSolicitud | None = None
    tipo: TipoAusencia | None = None
    empleado_id: uuid.UUID | None = None
    desde: date | None = None
    hasta: date | None = None


@dataclass(frozen=True, slots=True)
class AusenciaDTO:
    ausencia: Ausencia
    empleado_nombre: str
    empleado_color: str
    sector_nombre: str
    sector_color: str


@dataclass(frozen=True, slots=True)
class DescuentoRowDTO:
    """Fila del reporte mensual de descuentos: descuentos en días hábiles
    (paridad discountedReport legacy) + enfermedad/guardias en días corridos
    para las columnas extra del handoff."""

    empleado_id: uuid.UUID
    first_name: str
    last_name: str
    cargo_nombre: str
    dias_descontados: float
    dias_enfermedad: int
    guardias: int
