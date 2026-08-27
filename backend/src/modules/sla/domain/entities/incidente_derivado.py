from dataclasses import dataclass
from datetime import datetime

DIAS_ALERTA = 7


@dataclass(frozen=True, slots=True)
class IncidenteDerivado:
    """Incidente de Siges en estado 'Derivado' (`ID_Estado_Incidente=200`) —
    el operador le asignó un PST pero todavía no lo consultó con el técnico
    (pasa a 'En Curso', 300, recién cuando lo consulta). `id_tecnico` es
    `Incidente.ID_Tecnico`, el PST asignado."""

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
    dias_desde_ingreso: int

    @property
    def demorado(self) -> bool:
        return self.dias_desde_ingreso > DIAS_ALERTA
