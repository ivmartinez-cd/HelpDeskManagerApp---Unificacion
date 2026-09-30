from dataclasses import dataclass
from datetime import datetime

DIAS_ALERTA = 7


@dataclass(frozen=True, slots=True)
class IncidenteMesaAyuda:
    """Incidente de Siges asignado al técnico 'CD - Mesa de Ayuda'
    (`Incidente.ID_Tecnico`) que todavía no está cerrado/resuelto/anulado.

    `operador_login` es `Incidente.Usuario_Mod` — quién lo tocó último en
    Gestión, no una asignación formal de responsable (Siges no la modela)."""

    id_incidente: int
    fecha_ingreso: datetime | None
    tipo: str
    estado: str
    cliente: str
    sucursal: str
    nro_serie: str
    modelo: str
    operador_login: str
    operador: str
    dias_transcurridos: int
    # Visita de técnico más reciente en la misma sucursal (None = no hay) y
    # cuántas hay en total — ver sla/infrastructure/orion/sucursal_query.py.
    visita_id_incidente: int | None = None
    visita_tecnico: str | None = None
    visita_estado: str | None = None
    visitas_en_sucursal: int = 0

    @property
    def demorado(self) -> bool:
        return self.dias_transcurridos > DIAS_ALERTA
