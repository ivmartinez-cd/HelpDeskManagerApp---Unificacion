from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class IncidenteBono:
    """Un incidente individual de una de las 5 categorías del bono — el
    detalle que en "Tecnicos.xlsx" era cada fila de las tablas
    `Tabla_Consulta_desde_SiGesReadOnly_1`/`Tabla_DatosExternos_*`."""

    id_incidente: int
    categoria: str
    cliente: str
    sucursal: str
    nro_serie: str
    fecha_cierre: datetime | None = None
