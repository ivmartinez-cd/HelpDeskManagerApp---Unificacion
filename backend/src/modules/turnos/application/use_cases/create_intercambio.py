import uuid

from src.modules.turnos.application.dtos.turno_dtos import IntercambioCommand, IntercambioDTO
from src.modules.turnos.application.use_cases.intercambio_support import (
    IntercambioDependencies,
    armar_par,
    build_intercambio_dto,
    validar_campos_intercambio,
    validar_sin_solapamiento,
)


class CreateIntercambio:
    """Caso de uso: da de alta un intercambio de turnos (ADR-026) -- dos
    coberturas cruzadas con el mismo `intercambio_id`, en la misma
    transacción (límite de transacción por request de `get_db`). Cada lado
    valida solapamiento contra las coberturas activas de su ausente igual
    que una cobertura común."""

    def __init__(self, deps: IntercambioDependencies) -> None:
        self._deps = deps

    async def execute(self, command: IntercambioCommand) -> IntercambioDTO:
        validar_campos_intercambio(command)
        intercambio_id = uuid.uuid4()
        par = armar_par(
            command, intercambio_id, (uuid.uuid4(), uuid.uuid4()), command.created_by_user_id
        )
        for override in par:
            await validar_sin_solapamiento(self._deps.overrides, override, excluir_ids=set())
        for override in par:
            await self._deps.overrides.create(override)
        return await build_intercambio_dto(self._deps.users, intercambio_id, list(par))
