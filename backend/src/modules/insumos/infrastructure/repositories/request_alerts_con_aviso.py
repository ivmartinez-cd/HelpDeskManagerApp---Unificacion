"""Decorador del repositorio de alertas de solicitudes sin cargar que, cuando
una alerta escala, avisa en la campanita de la app (ADR-041): una notificación
por alerta y por escalada, para quienes tengan `insumos.view`. Reemplaza al
aviso de escritorio que antes armaba el dashboard de Insumos en el navegador.

Escalan dos caminos (`ListAlerts` al pollear la pantalla y el job
`SyncPendingAlerts`); los dos pasan por `escalate_due`, así que el aviso sale
de acá una sola vez. Publicar todas las escaladas es idempotente por clave
(`hp_request_id` + momento de la escalada): las que ya tenían aviso no se
repiten y una alerta que se resuelve y vuelve a escalar avisa de nuevo."""

from collections.abc import Sequence
from datetime import datetime

from src.modules.insumos.domain.entities.request_alert import AlertPendingEntry, RequestAlert
from src.modules.insumos.domain.repositories.request_alert_repository import (
    RequestAlertRepository,
)
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion
from src.modules.notificaciones.domain.repositories.notificacion_repository import (
    PublicadorNotificaciones,
)
from src.modules.notificaciones.domain.value_objects.audiencia import audiencia_permiso


def _aviso(alerta: RequestAlert) -> NuevaNotificacion:
    escalada = alerta.escalated_at.isoformat() if alerta.escalated_at else "-"
    insumo = alerta.description or alerta.sku or "insumo"
    url = f"/insumos?customerId={alerta.customer_id}" if alerta.customer_id else "/insumos"
    return NuevaNotificacion(
        clave=f"insumos.alerta:{alerta.hp_request_id}:{escalada}",
        audiencia=audiencia_permiso(VIEW),
        titulo=f"Solicitud de insumo sin cargar: {alerta.customer_name}",
        cuerpo=f"{insumo}. Superó el tiempo de espera y todavía no se cargó el pedido.",
        url=url,
    )


class RequestAlertsConAviso:
    def __init__(self, inner: RequestAlertRepository, publicador: PublicadorNotificaciones) -> None:
        self._inner = inner
        self._publicador = publicador

    async def escalate_due(self, cutoff: datetime) -> int:
        escaladas = await self._inner.escalate_due(cutoff)
        if escaladas:
            activas = await self._inner.list_escalated()
            await self._publicador.publicar([_aviso(a) for a in activas])
        return escaladas

    async def sync_pending(self, pending: list[AlertPendingEntry]) -> None:
        await self._inner.sync_pending(pending)

    async def list_escalated(self) -> list[RequestAlert]:
        return await self._inner.list_escalated()

    async def acknowledge(self, hp_request_ids: Sequence[int]) -> int:
        return await self._inner.acknowledge(hp_request_ids)
