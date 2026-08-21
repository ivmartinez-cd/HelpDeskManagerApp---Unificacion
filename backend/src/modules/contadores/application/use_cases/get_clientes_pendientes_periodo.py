"""Card de Inicio: cantidad estable de clientes con anexo pendiente de
EXACTAMENTE el período inmediato anterior al mes en curso (arrastre real del
cierre que acaba de pasar), independiente del backlog de calendario de
Gestión — ver `ClientesPendientesPeriodo`."""

import logging

from src.modules.contadores.domain.entities.clientes_pendientes_periodo import (
    ClientesPendientesPeriodo,
)
from src.modules.contadores.domain.ports.clientes_pendientes_periodo_port import (
    ClientesPendientesPeriodoPort,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class GetClientesPendientesPeriodo:
    def __init__(self, port: ClientesPendientesPeriodoPort) -> None:
        self._port = port

    async def execute(self) -> ClientesPendientesPeriodo | None:
        """`None` si Siges no responde: no hay señal, no se inventa un cero
        (mismo criterio que `FiltrarPendientesPorPeriodoReal`)."""
        try:
            return await self._port.contar()
        except ExternalServiceError as exc:
            logger.warning(
                "Sin cruce contra Siges; la card de Inicio no puede mostrar el "
                "arrastre del cierre anterior",
                exc_info=exc,
            )
            return None
