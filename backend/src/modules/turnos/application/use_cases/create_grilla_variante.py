import uuid

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    CreateGrillaVarianteCommand,
    GrillaVarianteDTO,
)
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
    build_grilla_variante_dto,
    build_variante_slots,
    calcular_advertencias,
    validar_variante,
)
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante


class CreateGrillaVariante:
    """Caso de uso: da de alta una grilla de vacaciones (ADR-025). No toca
    `turno_slot`/`turno_asignacion` -- se resuelve en lectura. Las
    advertencias (huecos, franjas sin operador, cubrientes ausentes) vuelven
    en el DTO pero no bloquean."""

    def __init__(self, deps: GrillaVarianteDependencies) -> None:
        self._deps = deps

    async def execute(self, command: CreateGrillaVarianteCommand) -> GrillaVarianteDTO:
        variante = GrillaVariante(
            id=uuid.uuid4(),
            motivo=command.motivo,
            origen_texto=command.origen_texto,
            desde=command.desde,
            hasta=command.hasta,
            estado="ACTIVA",
            created_by_user_id=command.created_by_user_id,
            slots=build_variante_slots(command.slots),
        )
        await validar_variante(self._deps, variante)
        await self._deps.variantes.create(variante)
        advertencias = await calcular_advertencias(self._deps, variante)
        return await build_grilla_variante_dto(self._deps, variante, advertencias)
