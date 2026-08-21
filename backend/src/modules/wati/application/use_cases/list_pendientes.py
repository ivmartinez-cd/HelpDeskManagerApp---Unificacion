from collections.abc import Callable
from datetime import UTC, datetime

from src.modules.wati.application.dtos.pendientes_dtos import ConversacionPendienteDto
from src.modules.wati.domain.entities.conversacion import ConversacionWati
from src.modules.wati.domain.repositories.conversacion_repository import (
    ConversacionRepository,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_dto(c: ConversacionWati, ahora: datetime) -> ConversacionPendienteDto:
    assert c.esperando_desde is not None  # garantizado por list_esperando
    return ConversacionPendienteDto(
        wa_id=c.wa_id,
        nombre=c.nombre,
        operador_nombre=c.operador_nombre,
        operador_email=c.operador_email,
        sin_asignar=c.sin_asignar,
        esperando_desde=c.esperando_desde,
        minutos_esperando=c.minutos_esperando(ahora),
        ultimo_mensaje_cliente_at=c.ultimo_mensaje_cliente_at,
        ultimo_texto_cliente=c.ultimo_texto_cliente,
    )


class ListPendientes:
    """Chats esperando respuesta humana, de la más antigua a la más nueva.
    Lee el estado sincronizado — nunca llama a WATI."""

    def __init__(
        self, repo: ConversacionRepository, reloj: Callable[[], datetime] = _utcnow
    ) -> None:
        self._repo = repo
        self._reloj = reloj

    async def execute(self) -> list[ConversacionPendienteDto]:
        ahora = self._reloj()
        esperando = await self._repo.list_esperando(ahora)
        return [_to_dto(c, ahora) for c in esperando if c.espera_respuesta(ahora)]
