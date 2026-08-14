from dataclasses import dataclass

from src.modules.preventivos.domain.entities.zona_parque import ZonaParque
from src.modules.preventivos.domain.repositories.preventivos_query_gateway import (
    PreventivosQueryGateway,
)
from src.modules.preventivos.domain.services.zonas import zona_excluida


@dataclass(frozen=True, slots=True)
class ListZonasDependencies:
    gateway: PreventivosQueryGateway
    zonas_excluidas: tuple[str, ...]


class ListZonasUseCase:
    """Catálogo de zonas locales: DISTINCT real de `Sucursal.Cuadricula` en
    Siges menos la lista de exclusión configurable — nunca un enum hardcodeado
    (si mañana aparece NORTE5, se muestra sola)."""

    def __init__(self, deps: ListZonasDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[ZonaParque]:
        zonas = await self._deps.gateway.list_zonas()
        visibles = [
            z for z in zonas if not zona_excluida(z.zona, self._deps.zonas_excluidas)
        ]
        return sorted(visibles, key=lambda z: z.zona)
