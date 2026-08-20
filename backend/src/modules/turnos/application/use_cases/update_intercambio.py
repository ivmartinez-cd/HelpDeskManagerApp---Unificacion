from src.modules.turnos.application.dtos.turno_dtos import IntercambioCommand, IntercambioDTO
from src.modules.turnos.application.use_cases.intercambio_support import (
    IntercambioDependencies,
    armar_par,
    build_intercambio_dto,
    validar_campos_intercambio,
    validar_sin_solapamiento,
)
from src.modules.turnos.domain.errors import IntercambioNotFoundError, OverrideNoEditableError


class UpdateIntercambio:
    """Caso de uso: edita un intercambio ACTIVO in-place (ADR-026) -- las dos
    coberturas conservan sus ids, `created_by_user_id` e `intercambio_id`;
    se reemplazan operadores, rango, alcances y motivo. Un intercambio con
    alguna mitad cancelada es historial y no se edita (mismo criterio que
    la edición de coberturas del 2026-08-14)."""

    def __init__(self, deps: IntercambioDependencies) -> None:
        self._deps = deps

    async def execute(self, command: IntercambioCommand) -> IntercambioDTO:
        if command.intercambio_id is None:
            raise IntercambioNotFoundError()
        existentes = await self._deps.overrides.list_by_intercambio(command.intercambio_id)
        if len(existentes) != 2:
            raise IntercambioNotFoundError()
        if any(o.estado != "ACTIVA" for o in existentes):
            raise OverrideNoEditableError()
        validar_campos_intercambio(command)

        ids = (existentes[0].id, existentes[1].id)
        par = armar_par(command, command.intercambio_id, ids, existentes[0].created_by_user_id)
        for override in par:
            await validar_sin_solapamiento(self._deps.overrides, override, excluir_ids=set(ids))
        for override in par:
            await self._deps.overrides.update(override)
        return await build_intercambio_dto(self._deps.users, command.intercambio_id, list(par))
