"""Puerto de alertas agrupadas sobre varios incidentes (observaciones /
observacion_incidentes)."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.observacion import Observacion
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    ObservacionGenerada,
)


class ObservacionRepository(Protocol):
    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Observacion]: ...

    async def update_estado(
        self, liquidacion_id: UUID, observacion_id: UUID, estado: str
    ) -> Observacion | None:
        """None si la observación no existe o no pertenece a esa liquidación."""
        ...

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, observaciones: Sequence[ObservacionGenerada]
    ) -> list[Observacion]:
        """Borra las observaciones (y sus filas `observacion_incidentes`) previas de
        la liquidación y crea las nuevas — mismo comportamiento idempotente que
        `AlertaRepository.replace_for_liquidacion`."""
        ...
