from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import SetPrestadorActiveCommand
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository


@dataclass(frozen=True, slots=True)
class SetPrestadorActiveDependencies:
    prestadores: PrestadorRepository


class SetPrestadorActive:
    """Caso de uso: alta/baja de un PST (ej. el "NO USAR" de Siges, o un PST
    que dejó de operar). No toca la asignación de operador ni el historial —
    un PST inactivo conserva su último operador para cuando se reactive."""

    def __init__(self, deps: SetPrestadorActiveDependencies) -> None:
        self._deps = deps

    async def execute(self, command: SetPrestadorActiveCommand) -> None:
        existing = await self._deps.prestadores.get_by_id(command.prestador_id)
        if existing is None:
            raise PrestadorNotFoundError()

        prestador = Prestador(
            id=existing.id,
            siges_empresa_id=existing.siges_empresa_id,
            den_comercial=existing.den_comercial,
            razon_social=existing.razon_social,
            cuit=existing.cuit,
            operador_id=existing.operador_id,
            is_active=command.is_active,
        )
        await self._deps.prestadores.save(prestador)
