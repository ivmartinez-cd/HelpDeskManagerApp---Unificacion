from typing import Protocol

from src.modules.contadores.domain.entities.estado_proceso_anexo import (
    EstadoProcesoAnexosSnapshot,
)


class EstadoProcesoAnexosPort(Protocol):
    """Puerto del estado real de proceso de facturación por anexo de Siges
    (ver `estado_proceso_anexo.py`). Universo completo de anexos de Impresión
    activos, cada uno anotado con su último período procesado — el caso de
    uso decide qué hacer con eso, para no disparar otra consulta a Siges por
    cada cruce."""

    async def list_estado(
        self, *, force_refresh: bool = False
    ) -> EstadoProcesoAnexosSnapshot: ...
