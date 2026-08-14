from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class IncidenteSinCerrar:
    """Incidente en estado 'Finalizado' (ID_Estado_Incidente=500) de Siges —
    el técnico lo completó pero todavía no fue cerrado en Gestión."""

    id_incidente: int
    fecha_ingreso: datetime | None
    tipo: str
    estado: str
    cliente: str
    sucursal: str
    nro_serie: str
    modelo: str
    tecnico: str
    id_tecnico: int
    fecha_finalizacion: datetime | None
    dias_en_estado: int
