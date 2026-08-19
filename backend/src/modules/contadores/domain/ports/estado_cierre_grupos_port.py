from typing import Protocol

from src.modules.contadores.domain.entities.estado_cierre_grupo import (
    EstadoCierreGruposSnapshot,
)


class EstadoCierreGruposPort(Protocol):
    """Puerto del estado real de cierre por grupo económico de Siges (ver
    `estado_cierre_grupo.py`). Universo completo de grupos con anexos de
    Impresión activos, cada uno anotado con si sigue sin cerrar — el caso de
    uso decide qué hacer con eso, para no disparar otra consulta a Siges por
    cada cruce."""

    async def list_estado(
        self, *, force_refresh: bool = False
    ) -> EstadoCierreGruposSnapshot: ...
