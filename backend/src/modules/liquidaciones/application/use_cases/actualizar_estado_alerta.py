"""ActualizarEstadoAlerta — la TL cambia el estado de una alerta y, con eso,
recalcula `estado_validacion` del incidente dueño: pasa a "ok" si ya no le
queda ninguna alerta pendiente/en revisión, o vuelve a "con_alertas" si se
reabre una que ya estaba cerrada. Ver `recalcular_estado_incidente`.

ALT005 agrupada: el frontend oculta la alerta individual (`es_grupo=False`)
cuando ya hay una de grupo para el mismo incidente (mismo hallazgo, evita
gestionarlo dos veces — ver `alerta-sub-row.tsx`). Para que esa individual
oculta no quede huérfana sin poder cerrarse nunca, gestionar la de grupo le
aplica en cascada el mismo estado/justificación (`_cascada_grupo_alt005`)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.errors import IncidenteRelacionadoInvalidoError
from src.modules.liquidaciones.domain.repositories.alerta_repository import AlertaRepository
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.services.triage_alertas import recalcular_estado_incidente

_CODIGO_ALT005 = "ALT005"


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
        if actualizada is None:
            return None
        afectados = {actualizada.incidente_id}
        afectados |= await self._cascada_grupo_alt005(liquidacion_id, actualizada)
        await self._recalcular_estados(liquidacion_id, afectados)
        return actualizada

    async def _validar_incidente_relacionado(
        self, liquidacion_id: UUID, incidente_relacionado_id: UUID | None
    ) -> None:
        if incidente_relacionado_id is None:
            return
        incidentes_liq = await self._ports.incidentes.list_by_liquidacion(liquidacion_id)
        if not any(i.id == incidente_relacionado_id for i in incidentes_liq):
            raise IncidenteRelacionadoInvalidoError(incidente_relacionado_id)

    async def _cascada_grupo_alt005(self, liquidacion_id: UUID, grupo: Alerta) -> set[UUID]:
        if not grupo.es_grupo or grupo.tipo_alerta != _CODIGO_ALT005:
            return set()
        hermanas = await self._ports.alertas.list_by_liquidacion(liquidacion_id)
        individuales = [
            h
            for h in hermanas
            if h.tipo_alerta == _CODIGO_ALT005
            and not h.es_grupo
            and h.incidente_id in grupo.grupo_incidente_ids
            and h.estado != grupo.estado
        ]
        for h in individuales:
            await self._ports.alertas.update_estado(
                liquidacion_id,
                h.id,
                estado=grupo.estado,
                justificacion=grupo.justificacion,
                incidente_relacionado_id=h.incidente_relacionado_id,
            )
        return {h.incidente_id for h in individuales}

    async def _recalcular_estados(self, liquidacion_id: UUID, incidente_ids: set[UUID]) -> None:
        hermanas = await self._ports.alertas.list_by_liquidacion(liquidacion_id)
        for incidente_id in incidente_ids:
            estados = [a.estado for a in hermanas if a.incidente_id == incidente_id]
            nuevo_estado = recalcular_estado_incidente(estados)
            await self._ports.incidentes.update_estado_validacion(incidente_id, nuevo_estado)
