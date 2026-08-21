from typing import Protocol

from src.modules.contadores.domain.entities.clientes_pendientes_periodo import (
    ClientesPendientesPeriodo,
)


class ClientesPendientesPeriodoPort(Protocol):
    """Puerto del arrastre real de cierre del período inmediato anterior (ver
    `clientes_pendientes_periodo.py`)."""

    async def contar(self, *, force_refresh: bool = False) -> ClientesPendientesPeriodo: ...
