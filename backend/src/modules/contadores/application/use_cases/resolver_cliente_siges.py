"""Resolución de clientes sin cruce (aparecen todos los meses en Gestión):
buscar empresas en Siges con el parque a la vista, y guardar el mapeo
cliente → empresa(s) que el cruce automático no pudo deducir. El mapeo
alimenta a cliente_matcher, donde el alias siempre gana."""

from dataclasses import dataclass

from src.modules.contadores.domain.ports.parque_cliente_port import (
    EmpresaConParque,
    ParqueClientePort,
)
from src.modules.contadores.domain.repositories.cliente_siges_map_repository import (
    ClienteSigesMapRepository,
)


class SearchEmpresasSiges:
    """Búsqueda en vivo para el modal de resolución."""

    def __init__(self, parque: ParqueClientePort) -> None:
        self._parque = parque

    async def execute(self, texto: str) -> list[EmpresaConParque]:
        return await self._parque.search_empresas_activas(texto)


@dataclass(frozen=True, slots=True)
class SetClienteSigesMapCommand:
    cliente_gestion: str
    siges_empresa_ids: list[int]
    """Vacía = desmapear el cliente (vuelve a 'sin cruce')."""


class SetClienteSigesMap:
    def __init__(self, alias: ClienteSigesMapRepository) -> None:
        self._alias = alias

    async def execute(self, command: SetClienteSigesMapCommand) -> None:
        await self._alias.replace(
            command.cliente_gestion.strip(), command.siges_empresa_ids
        )
