from dataclasses import dataclass, field

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.domain.entities.anexo_pendiente import AnexoPendiente
from src.modules.contadores.domain.services.periodos_facturacion import EstadoAnexoPendiente


@dataclass(frozen=True)
class AnexoPendienteConEstado:
    """Anexo pendiente anotado con su estado EN PROCESO/DEMORADO y el operador
    del calendario asignado al cliente. `operador=None` cuando el cliente no
    cruza con el calendario o el cruce no pudo armarse (Siges caído)."""

    anexo: AnexoPendiente
    estado: EstadoAnexoPendiente
    operador: OperadorAsignado | None = field(default=None)
