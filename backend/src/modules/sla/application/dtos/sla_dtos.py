from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class GetSlaComplianceRequest:
    periodo: int


@dataclass(frozen=True, slots=True)
class TecnicoVencidosDTO:
    """Un grupo de la tabla de vencidos: técnico/PST con sus IDs de incidente,
    igual que el desglose de la tabla dinámica de Excel que se reemplaza."""

    tecnico: str
    cantidad: int
    ids_incidente: list[int]


@dataclass(frozen=True, slots=True)
class SlaComplianceResult:
    periodo: int
    total: int
    correctos: int
    vencidos: int
    pct_correctos: float
    pct_vencidos: float
    vencidos_por_tecnico: list[TecnicoVencidosDTO]


@dataclass(frozen=True, slots=True)
class IncidenteVencidoDTO:
    id_incidente: int
    tecnico: str
    region: str
    cliente: str
    sucursal: str
    modelo: str
    nro_serie: str
    fecha_ingreso: datetime | None
    fecha_operativo: datetime | None
    tiempo: str
    rango: str
    sla_horas: int
    horas_vencido: int
