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
    # Caso abierto de Mesa de Ayuda en la misma sucursal (None = no hay) y
    # cuántos hay — ver sla/infrastructure/orion/sucursal_query.py.
    mda_id_incidente: int | None = None
    casos_mda_en_sucursal: int = 0

    @property
    def demorado(self) -> bool:
        return self.dias_desde_ingreso > DIAS_ALERTA
