from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.wati.domain.entities.conversacion import HORAS_EXPIRACION, ConversacionWati
from src.modules.wati.infrastructure.models.conversacion_model import ConversacionWatiModel

_CAMPOS = (
    "nombre",
    "conversation_id",
    "ticket_id",
    "operador_nombre",
    "operador_email",
    "ultimo_mensaje_cliente_at",
    "esperando_desde",
    "ultima_respuesta_at",
    "ultimo_bot_at",
    "cerrada_at",
    "bot_activo",
    "ultimo_texto_cliente",
    "sincronizado_at",
)


def _to_row(c: ConversacionWati) -> dict[str, object]:
    return {"wa_id": c.wa_id, **{campo: getattr(c, campo) for campo in _CAMPOS}}


def _to_entity(m: ConversacionWatiModel) -> ConversacionWati:
    return ConversacionWati(wa_id=m.wa_id, **{campo: getattr(m, campo) for campo in _CAMPOS})


class SqlAlchemyConversacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, conversacion: ConversacionWati) -> None:
        row = _to_row(conversacion)
        stmt = insert(ConversacionWatiModel).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["wa_id"], set_={k: v for k, v in row.items() if k != "wa_id"}
        )
        await self._session.execute(stmt)

    async def list_activas(self, desde: datetime) -> list[ConversacionWati]:
        stmt = select(ConversacionWatiModel).where(
            or_(
                ConversacionWatiModel.ultimo_mensaje_cliente_at >= desde,
                ConversacionWatiModel.esperando_desde.is_not(None),
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def list_esperando(self, ahora: datetime) -> list[ConversacionWati]:
        limite = ahora - timedelta(hours=HORAS_EXPIRACION)
        stmt = (
            select(ConversacionWatiModel)
            .where(
                ConversacionWatiModel.esperando_desde.is_not(None),
                ConversacionWatiModel.cerrada_at.is_(None),
                ConversacionWatiModel.bot_activo.is_(False),
                ConversacionWatiModel.ultimo_mensaje_cliente_at >= limite,
            )
            .order_by(ConversacionWatiModel.esperando_desde.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_ultima_sincronizacion(self) -> datetime | None:
        stmt = select(func.max(ConversacionWatiModel.sincronizado_at))
        return (await self._session.execute(stmt)).scalar_one_or_none()
