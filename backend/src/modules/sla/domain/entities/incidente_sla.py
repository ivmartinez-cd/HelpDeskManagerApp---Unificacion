from dataclasses import dataclass
from datetime import datetime

RESULTADO_CORRECTO = "Correcto"
RESULTADO_VENCIDO = "Vencido"


@dataclass(frozen=True, slots=True)
class IncidenteSla:
    """Una fila de la consulta de cumplimiento contra Siges (incidente + su
    registro de IncidenteTiempo). `resultado`, `horas_vencido` y `rango` vienen
    ya calculados por la consulta legacy — acá solo se agrega y filtra, no se
    recalculan, para no divergir de la planilla que este módulo reemplaza."""

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
    region: str
    fecha_operativo: datetime | None
    periodo: int
    tiempo: str
    rango: str
    sla_horas: int
    horas_vencido: int
    resultado: str

    @property
    def es_vencido(self) -> bool:
        return self.resultado == RESULTADO_VENCIDO
