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

    @property
    def demorado(self) -> bool:
        return self.dias_transcurridos > DIAS_ALERTA
