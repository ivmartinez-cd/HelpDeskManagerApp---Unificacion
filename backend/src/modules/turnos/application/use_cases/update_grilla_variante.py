from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    GrillaVarianteDTO,
    UpdateGrillaVarianteCommand,
)
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
    build_grilla_variante_dto,
    build_variante_slots,
    calcular_advertencias,
    validar_variante,
)
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante
from src.modules.turnos.domain.errors import (
    GrillaVarianteNotFoundError,
    VarianteNoEditableError,
)


class UpdateGrillaVariante:
    """Caso de uso: edita una grilla de vacaciones ACTIVA in-place (mismo
    `id`, reemplazo completo de cabecera + franjas + asignaciones -- mismo
    criterio que la edición de overrides ADR-013 del 2026-08-14). Una
    CANCELADA es un registro histórico; `estado` y `created_by_user_id` no
    cambian."""

    def __init__(self, deps: GrillaVarianteDependencies) -> None:
        self._deps = deps

    async def execute(self, command: UpdateGrillaVarianteCommand) -> GrillaVarianteDTO:
        existing = await self._deps.variantes.get_by_id(command.variante_id)
        if existing is None:
            raise GrillaVarianteNotFoundError()
        if existing.estado != "ACTIVA":
            raise VarianteNoEditableError()
        variante = GrillaVariante(
            id=existing.id,
            motivo=command.motivo,
            origen_texto=command.origen_texto,
            desde=command.desde,
            hasta=command.hasta,
            estado="ACTIVA",
            created_by_user_id=existing.created_by_user_id,
            slots=build_variante_slots(command.slots),
        )
        await validar_variante(self._deps, variante, excluir_id=existing.id)
        await self._deps.variantes.update(variante)
        advertencias = await calcular_advertencias(self._deps, variante)
        return await build_grilla_variante_dto(self._deps, variante, advertencias)
