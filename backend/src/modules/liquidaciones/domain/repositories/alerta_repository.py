"""Puerto de alertas generadas por el motor de reglas (alertas)."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.services.conciliar_alertas import AlertaConciliada


class AlertaRepository(Protocol):
    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Alerta]: ...

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, alertas: Sequence[AlertaConciliada]
    ) -> list[Alerta]:
        """Borra las alertas previas de la liquidación y crea las nuevas — mismo
        comportamiento idempotente de `ejecutar_motor` del legacy. La decisión de
        la TL sobrevive porque cada `AlertaConciliada` ya trae el estado y la
        justificación preservados (ver `conciliar_alertas`)."""
        ...

    async def update_estado(
        self,
        liquidacion_id: UUID,
        alerta_id: UUID,
        *,
        estado: str,
        justificacion: str | None,
        incidente_relacionado_id: UUID | None = None,
    ) -> Alerta | None:
        """Cambia estado, justificación e incidente relacionado (los tres siempre
        se pisan con lo que venga — None limpia al reabrir). None si la alerta no
        existe o no pertenece a la liquidación."""
        ...
