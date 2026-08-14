from dataclasses import dataclass

from src.modules.contadores.domain.entities.anexo_pendiente import AnexoPendiente
from src.modules.contadores.domain.services.periodos_facturacion import EstadoAnexoPendiente


@dataclass(frozen=True)
class AnexoPendienteConEstado:
    """Anexo pendiente anotado con su estado EN PROCESO/DEMORADO — el estado
    se deriva del calendario en el momento de listar (no se persiste ni se
    cachea junto al snapshot, que puede cruzar un cambio de mes)."""

    anexo: AnexoPendiente
    estado: EstadoAnexoPendiente
