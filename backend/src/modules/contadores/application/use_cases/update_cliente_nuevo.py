import uuid

from src.modules.contadores.application.dtos.cliente_nuevo_dtos import (
    ClienteNuevoRequest,
    ClienteNuevoResult,
)
from src.modules.contadores.application.use_cases._cliente_nuevo_mapper import (
    aplicar_request,
    to_cliente_nuevo_result,
)
from src.modules.contadores.domain.errors import (
    ClienteNuevoNotFoundError,
    DuplicateClienteNuevoError,
)
from src.modules.contadores.domain.repositories.cliente_nuevo_repository import (
    ClienteNuevoRepository,
)


class UpdateClienteNuevoUseCase:
    def __init__(self, repo: ClienteNuevoRepository) -> None:
        self._repo = repo

    async def execute(
        self, ficha_id: uuid.UUID, request: ClienteNuevoRequest
    ) -> ClienteNuevoResult:
        ficha = await self._repo.get_by_id(ficha_id)
        if ficha is None:
            raise ClienteNuevoNotFoundError()
        otra = await self._repo.get_abierta_by_cliente(request.cliente)
        if otra is not None and otra.id != ficha.id:
            raise DuplicateClienteNuevoError(request.cliente.strip())
        aplicar_request(ficha, request)
        await self._repo.save(ficha)
        return to_cliente_nuevo_result(ficha, None)


class DeleteClienteNuevoUseCase:
    def __init__(self, repo: ClienteNuevoRepository) -> None:
        self._repo = repo

    async def execute(self, ficha_id: uuid.UUID) -> None:
        if await self._repo.get_by_id(ficha_id) is None:
            raise ClienteNuevoNotFoundError()
        await self._repo.delete(ficha_id)
