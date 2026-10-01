"""Estado de las conversaciones de WATI contra Postgres."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.wati.domain.entities.conversacion import HORAS_EXPIRACION, ConversacionWati
from src.modules.wati.infrastructure.repositories.sqlalchemy_conversacion_repository import (
    SqlAlchemyConversacionRepository,
)

_AHORA = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def _conversacion(**overrides: object) -> ConversacionWati:
    base = ConversacionWati(
        wa_id=uuid.uuid4().hex[:12],
        nombre="Cliente",
        conversation_id=None,
        ticket_id=None,
        operador_nombre=None,
        operador_email=None,
        ultimo_mensaje_cliente_at=_AHORA - timedelta(hours=1),
        esperando_desde=_AHORA - timedelta(hours=1),
        ultima_respuesta_at=None,
        ultimo_bot_at=None,
        cerrada_at=None,
        bot_activo=False,
        ultimo_texto_cliente="hola",
        sincronizado_at=_AHORA,
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


async def test_upsert_inserta_y_despues_actualiza(db_session: AsyncSession) -> None:
    repo = SqlAlchemyConversacionRepository(db_session)
    original = _conversacion()

    await repo.upsert(original)
    await repo.upsert(replace(original, nombre="Renombrado", sincronizado_at=_AHORA + timedelta(1)))

    activas = {c.wa_id: c for c in await repo.list_activas(_AHORA - timedelta(days=1))}
    assert activas[original.wa_id].nombre == "Renombrado"
    assert await repo.get_ultima_sincronizacion() == _AHORA + timedelta(days=1)


async def test_list_esperando_excluye_cerradas_bot_y_vencidas_y_ordena(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyConversacionRepository(db_session)
    vieja = _conversacion(esperando_desde=_AHORA - timedelta(hours=3))
    nueva = _conversacion()
    descartadas = [
        _conversacion(cerrada_at=_AHORA),
        _conversacion(bot_activo=True),
        _conversacion(esperando_desde=None),
        _conversacion(ultimo_mensaje_cliente_at=_AHORA - timedelta(hours=HORAS_EXPIRACION + 1)),
    ]
    for c in [nueva, vieja, *descartadas]:
        await repo.upsert(c)

    esperando = [c.wa_id for c in await repo.list_esperando(_AHORA)]

    assert esperando == [vieja.wa_id, nueva.wa_id]
