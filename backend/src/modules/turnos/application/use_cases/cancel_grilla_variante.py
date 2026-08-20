import uuid

from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
)
from src.modules.turnos.domain.errors import GrillaVarianteNotFoundError


class CancelGrillaVariante:
    """Caso de uso: cancela una grilla de vacaciones antes de que venza. Sin
    `DELETE` -- la cancelación es la única reversión anticipada, para no
    perder el registro de que existió (ADR-025, mismo criterio que ADR-013).
    Cancelar una ya cancelada es idempotente."""

    def __init__(self, deps: GrillaVarianteDependencies) -> None:
        self._deps = deps

    async def execute(self, variante_id: uuid.UUID) -> None:
        existing = await self._deps.variantes.get_by_id(variante_id)
        if existing is None:
            raise GrillaVarianteNotFoundError()
        await self._deps.variantes.cancelar(variante_id)
