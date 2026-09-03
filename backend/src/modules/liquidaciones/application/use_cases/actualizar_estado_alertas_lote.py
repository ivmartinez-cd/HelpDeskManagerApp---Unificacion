"""ActualizarEstadoAlertasLote — la TL resuelve/descarta/revisa varias alertas
de una liquidación con el mismo motivo en una sola operación (caso típico: toda
la liquidación de una zona cobrada a costo doble, antes se gestionaba una por una
repitiendo la misma justificación).

Mismo efecto que `ActualizarEstadoAlerta` repetido, con dos diferencias:
- el lote se valida entero antes de tocar nada (una alerta ajena → error y no
  se cambia ninguna);
- `incidente_relacionado_id` de cada alerta se preserva (el update del
  repositorio lo pisa con lo que recibe, y en lote no hay un vínculo único).

Al final recalcula `estado_validacion` de cada incidente afectado una sola vez.
"""

from collections import defaultdict
from uuid import UUID

from src.modules.liquidaciones.application.use_cases.actualizar_estado_alerta import (
    ActualizarEstadoAlertaPorts,
)
from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.errors import AlertasNoEncontradasError
from src.modules.liquidaciones.domain.services.triage_alertas import recalcular_estado_incidente


class ActualizarEstadoAlertasLote:
    def __init__(self, ports: ActualizarEstadoAlertaPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        liquidacion_id: UUID,
        alerta_ids: list[UUID],
        *,
        estado: str,
        justificacion: str | None,
    ) -> list[Alerta]:
        vigentes = await self._ports.alertas.list_by_liquidacion(liquidacion_id)
        existentes = {a.id: a for a in vigentes}
        faltantes = [i for i in alerta_ids if i not in existentes]
        if faltantes:
            raise AlertasNoEncontradasError(faltantes)
        # dict.fromkeys: dedup preservando el orden pedido.
        elegidas = [existentes[i] for i in dict.fromkeys(alerta_ids)]
        actualizadas = await self._actualizar(liquidacion_id, elegidas, estado, justificacion)
        await self._recalcular_incidentes(liquidacion_id, {a.incidente_id for a in actualizadas})
        return actualizadas

    async def _actualizar(
        self, liquidacion_id: UUID, alertas: list[Alerta], estado: str, justificacion: str | None
    ) -> list[Alerta]:
        actualizadas: list[Alerta] = []
        for alerta in alertas:
            resultado = await self._ports.alertas.update_estado(
                liquidacion_id,
                alerta.id,
                estado=estado,
                justificacion=justificacion,
                incidente_relacionado_id=alerta.incidente_relacionado_id,
            )
            if resultado is not None:
                actualizadas.append(resultado)
        return actualizadas

    async def _recalcular_incidentes(self, liquidacion_id: UUID, incidente_ids: set[UUID]) -> None:
        estados_por_incidente: dict[UUID, list[str]] = defaultdict(list)
        for a in await self._ports.alertas.list_by_liquidacion(liquidacion_id):
            estados_por_incidente[a.incidente_id].append(a.estado)
        for incidente_id in incidente_ids:
            nuevo_estado = recalcular_estado_incidente(estados_por_incidente[incidente_id])
            await self._ports.incidentes.update_estado_validacion(incidente_id, nuevo_estado)
