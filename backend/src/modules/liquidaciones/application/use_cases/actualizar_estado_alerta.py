"""ActualizarEstadoAlerta — la TL cambia el estado de una alerta y, con eso,
recalcula `estado_validacion` del incidente dueño: pasa a "ok" si ya no le
queda ninguna alerta pendiente/en revisión, o vuelve a "con_alertas" si se
reabre una que ya estaba cerrada. Ver `recalcular_estado_incidente`."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.errors import IncidenteRelacionadoInvalidoError
from src.modules.liquidaciones.domain.repositories.alerta_repository import AlertaRepository
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.services.triage_alertas import recalcular_estado_incidente


@dataclass(frozen=True)
class ActualizarEstadoAlertaPorts:
    alertas: AlertaRepository
    incidentes: IncidenteRepository


class ActualizarEstadoAlerta:
    def __init__(self, ports: ActualizarEstadoAlertaPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        liquidacion_id: UUID,
        alerta_id: UUID,
        *,
        estado: str,
        justificacion: str | None,
        incidente_relacionado_id: UUID | None = None,
    ) -> Alerta | None:
        await self._validar_incidente_relacionado(liquidacion_id, incidente_relacionado_id)
        actualizada = await self._ports.alertas.update_estado(
            liquidacion_id,
            alerta_id,
            estado=estado,
            justificacion=justificacion,
            incidente_relacionado_id=incidente_relacionado_id,
        )
        await self._recalcular_estado_incidente(liquidacion_id, actualizada)
        return actualizada

    async def _validar_incidente_relacionado(
        self, liquidacion_id: UUID, incidente_relacionado_id: UUID | None
    ) -> None:
        if incidente_relacionado_id is None:
            return
        incidentes_liq = await self._ports.incidentes.list_by_liquidacion(liquidacion_id)
        if not any(i.id == incidente_relacionado_id for i in incidentes_liq):
            raise IncidenteRelacionadoInvalidoError(incidente_relacionado_id)

    async def _recalcular_estado_incidente(
        self, liquidacion_id: UUID, actualizada: Alerta | None
    ) -> None:
        if actualizada is None:
            return
        hermanas = await self._ports.alertas.list_by_liquidacion(liquidacion_id)
        estados = [a.estado for a in hermanas if a.incidente_id == actualizada.incidente_id]
        nuevo_estado = recalcular_estado_incidente(estados)
        await self._ports.incidentes.update_estado_validacion(
            actualizada.incidente_id, nuevo_estado
        )
