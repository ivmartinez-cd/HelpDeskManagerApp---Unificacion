from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TecnicoVencidosSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tecnico: str
    id_tecnico: int
    cantidad: int
    ids_incidente: list[int]


class SlaResumenResponse(BaseModel):
    """Resumen de cumplimiento del período — no es una colección, no va en
    Page[T] (mismo criterio que statistics_router de insumos, §11)."""

    model_config = ConfigDict(from_attributes=True)

    periodo: int
    total: int
    correctos: int
    vencidos: int
    pct_correctos: float
    pct_vencidos: float
    vencidos_por_tecnico: list[TecnicoVencidosSchema]
    updated_at: datetime


class IncidenteVencidoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_incidente: int
    tecnico: str
    id_tecnico: int
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
