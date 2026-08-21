"""Un ciclo de sincronización contra WATI (polling; no hay webhook — ver
memoria del proyecto: IT no expone URL pública).

Lista de vigilancia = contactos cuyo `last_updated` cae en la ventana
(conversaciones nuevas: la API los devuelve ordenados por ese campo) ∪
conversaciones ya conocidas con actividad reciente o esperando respuesta
(para ver si les contestaron o las cerraron). Por cada una se piden los
últimos eventos y se rederiva el estado completo.

Tope de contactos por ciclo para respetar el rate limit de WATI
(10 req / 10 s): el gateway ya espacia las llamadas, el tope acota la
duración del ciclo. Lo que no entra se loguea y se revisa en el próximo."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from src.modules.wati.application.dtos.pendientes_dtos import SyncResultadoDto
from src.modules.wati.domain.repositories.conversacion_repository import (
    ConversacionRepository,
)
from src.modules.wati.domain.repositories.wati_gateway import WatiGateway
from src.modules.wati.domain.services.derivar_conversacion import derivar_conversacion

logger = logging.getLogger(__name__)

_CONTACTOS_PAGINA = 100
_EVENTOS_POR_CHAT = 40


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SyncConversaciones:
    def __init__(
        self,
        gateway: WatiGateway,
        repo: ConversacionRepository,
        *,
        ventana_horas: int = 48,
        max_por_ciclo: int = 60,
        reloj: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._gateway = gateway
        self._repo = repo
        self._ventana = timedelta(hours=ventana_horas)
        self._max = max_por_ciclo
        self._reloj = reloj

    async def execute(self) -> SyncResultadoDto:
        ahora = self._reloj()
        candidatos = await self._candidatos(ahora)
        a_revisar = list(candidatos.items())[: self._max]
        descartados = len(candidatos) - len(a_revisar)
        if descartados:
            logger.warning(
                "wati_sync: %d candidatos fuera del tope por ciclo",
                descartados,
                extra={"max_por_ciclo": self._max},
            )
        esperando = 0
        for wa_id, nombre in a_revisar:
            eventos = await self._gateway.get_eventos(wa_id, _EVENTOS_POR_CHAT)
            conv = derivar_conversacion(wa_id, nombre, eventos, ahora)
            await self._repo.upsert(conv)
            esperando += int(conv.espera_respuesta(ahora))
        return SyncResultadoDto(len(a_revisar), esperando, descartados)

    async def _candidatos(self, ahora: datetime) -> dict[str, str]:
        """wa_id → nombre, en orden de prioridad (lo más reciente primero)."""
        desde = ahora - self._ventana
        contactos = await self._gateway.list_contactos_recientes(_CONTACTOS_PAGINA)
        candidatos = {c.wa_id: c.nombre for c in contactos if c.last_updated >= desde}
        for conv in await self._repo.list_activas(desde):
            candidatos.setdefault(conv.wa_id, conv.nombre)
        return candidatos
