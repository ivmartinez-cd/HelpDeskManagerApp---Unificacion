"""Puerto de alertas generadas por el motor de reglas (alertas)."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada


class AlertaRepository(Protocol):
    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Alerta]: ...

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, alertas: Sequence[AlertaGenerada]
    ) -> list[Alerta]:
        """Borra las alertas (y sus resoluciones) previas de la liquidación y crea las
        nuevas — mismo comportamiento idempotente de `ejecutar_motor` del legacy:
        reanalizar nunca acumula, siempre reemplaza el set completo."""
        ...
