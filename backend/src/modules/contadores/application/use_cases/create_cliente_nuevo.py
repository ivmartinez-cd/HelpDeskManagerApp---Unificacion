import uuid

from src.modules.contadores.application.dtos.cliente_nuevo_dtos import (
    ClienteNuevoRequest,
    ClienteNuevoResult,
)
from src.modules.contadores.application.use_cases._cliente_nuevo_mapper import (
    aplicar_request,
    to_cliente_nuevo_result,
)
from src.modules.contadores.domain.entities.cliente_nuevo import ClienteNuevo
from src.modules.contadores.domain.errors import DuplicateClienteNuevoError
from src.modules.contadores.domain.repositories.cliente_nuevo_repository import (
    ClienteNuevoRepository,
)


class CreateClienteNuevoUseCase:
    """Da de alta una ficha. Rechaza una segunda ficha ABIERTA para el mismo
    cliente (una cerrada es histórico: un cliente puede volver a arrancar)."""

    def __init__(self, repo: ClienteNuevoRepository) -> None:
        self._repo = repo

    async def execute(
        self, request: ClienteNuevoRequest, *, created_by_user_id: uuid.UUID
    ) -> ClienteNuevoResult:
        if await self._repo.get_abierta_by_cliente(request.cliente) is not None:
            raise DuplicateClienteNuevoError(request.cliente.strip())
        ficha = ClienteNuevo(
            id=uuid.uuid4(), cliente=request.cliente.strip(), created_by_user_id=created_by_user_id
        )
        aplicar_request(ficha, request)
        await self._repo.add(ficha)
        return to_cliente_nuevo_result(ficha, None)
