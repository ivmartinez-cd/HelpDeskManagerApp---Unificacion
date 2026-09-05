import uuid
from dataclasses import dataclass

from src.modules.turnos.domain.errors import CasillaEnUsoError, CasillaNotFoundError
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository
from src.modules.turnos.domain.repositories.grilla_variante_repository import (
    GrillaVarianteRepository,
)
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository


@dataclass(frozen=True, slots=True)
class DeleteCasillaDependencies:
    casillas: CasillaRepository
    slots: SlotRepository
    variantes: GrillaVarianteRepository


class DeleteCasilla:
    """Caso de uso: elimina una casilla sin franjas. Con franjas titulares o
    referenciada por una grilla de vacaciones ACTIVA se rechaza: el CASCADE
    de la FK borraría en silencio franjas, asignaciones y filas de la
    variante (una ACTIVA podría quedar vacía)."""

    def __init__(self, deps: DeleteCasillaDependencies) -> None:
        self._deps = deps

    async def execute(self, casilla_id: uuid.UUID) -> None:
        if await self._deps.casillas.get_by_id(casilla_id) is None:
            raise CasillaNotFoundError(casilla_id)
        franjas = await self._deps.slots.list_by_casilla(casilla_id)
        if franjas:
            raise CasillaEnUsoError(
                f"tiene {len(franjas)} franja(s) titular(es); borrarlas primero"
            )
        variantes = await self._variantes_activas_que_la_usan(casilla_id)
        if variantes:
            raise CasillaEnUsoError(f"la referencia la grilla de vacaciones activa {variantes}")
        await self._deps.casillas.delete(casilla_id)

    async def _variantes_activas_que_la_usan(self, casilla_id: uuid.UUID) -> str:
        """Detalle legible de las variantes ACTIVAS con franjas en la casilla; '' si ninguna."""
        return ", ".join(
            f"{v.motivo or 'sin motivo'} ({v.desde:%d/%m/%Y}-{v.hasta:%d/%m/%Y})"
            for v in await self._deps.variantes.list_activas()
            if any(s.casilla_id == casilla_id for s in v.slots)
        )
