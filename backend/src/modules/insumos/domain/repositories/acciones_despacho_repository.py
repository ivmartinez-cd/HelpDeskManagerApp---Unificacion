"""Puertos de las acciones de operador y de las corridas del job de Despachados."""

from typing import Protocol

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    AccionRegistrada,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)


class AccionesDespachoRepository(Protocol):
    async def agregar(self, accion: AccionNueva) -> AccionRegistrada:
        """Guarda la acción; `id` y `creada_en` los pone la base."""
        ...

    async def listar_por_guia(self, guia: str) -> list[AccionRegistrada]:
        """De la más reciente a la más vieja."""
        ...


class CorridasDespachoRepository(Protocol):
    async def iniciar(self, origen: OrigenCorrida, usuario_nombre: str | None) -> Corrida: ...

    async def terminar(self, corrida_id: int, resumen: ResumenCorrida) -> None:
        """Marca la corrida como terminada ahora, con su resumen."""
        ...

    async def cerrar_interrumpidas(self, motivo: str) -> int:
        """Da por terminadas, con `motivo` como error, las corridas que quedaron sin
        terminar (el proceso se reinició a mitad de camino). Devuelve cuántas cerró."""
        ...

    async def ultima(self) -> Corrida | None:
        """La más reciente, terminada o en curso."""
        ...

    async def ultima_terminada(self) -> Corrida | None: ...
