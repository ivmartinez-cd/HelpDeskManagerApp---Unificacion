import unicodedata
import uuid
from datetime import date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.infrastructure.models.calendar_event_model import CalendarEventModel
from src.modules.contadores.infrastructure.models.operador_model import OperadorModel


def _normalize(text: str) -> str:
    """Compara nombres ignorando mayúsculas, acentos y espacios repetidos —
    el full_name de AppUser y el nombre scrapeado de Gestión rara vez
    coinciden byte a byte."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


class SqlAlchemyCalendarEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_events(
        self, *, start_date: str, end_date: str, operador_id: str | None
    ) -> list[CalendarEvent]:
        stmt = select(CalendarEventModel).where(
            CalendarEventModel.event_date >= date.fromisoformat(start_date),
            CalendarEventModel.event_date <= date.fromisoformat(end_date),
        )
        if operador_id is not None:
            stmt = stmt.where(CalendarEventModel.operador_id == operador_id)
        stmt = stmt.order_by(CalendarEventModel.event_date, CalendarEventModel.gestion_event_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return _dedupe_by_gestion_id([_to_entity(row) for row in rows])

    async def replace_events_in_range(
        self, *, start_date: str, end_date: str, events: list[CalendarEvent]
    ) -> None:
        """Full replace del rango completo (todos los operadores a la vez):
        cada evento trae su propio operador_id, así los cambios de operador
        en Gestión no dejan copias viejas bajo el operador anterior."""
        await self._session.execute(
            delete(CalendarEventModel).where(
                CalendarEventModel.event_date >= date.fromisoformat(start_date),
                CalendarEventModel.event_date <= date.fromisoformat(end_date),
            )
        )
        for event in events:
            self._session.add(_to_model(event, event.operador_id or ""))
        await self._session.flush()

    async def prune_operadores_not_in(self, operador_ids: list[str]) -> None:
        await self._session.execute(
            delete(CalendarEventModel).where(CalendarEventModel.operador_id.notin_(operador_ids))
        )
        await self._session.execute(
            delete(OperadorModel).where(OperadorModel.id.notin_(operador_ids))
        )
        await self._session.flush()

    async def list_operadores(self) -> list[Operador]:
        stmt = select(OperadorModel).order_by(OperadorModel.nombre)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [Operador(id=row.id, nombre=row.nombre, color=row.color) for row in rows]

    async def replace_operadores(self, operadores: list[Operador]) -> None:
        for operador in operadores:
            stmt = (
                pg_insert(OperadorModel)
                .values(id=operador.id, nombre=operador.nombre, color=operador.color)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "nombre": operador.nombre,
                        "color": operador.color,
                        "updated_at": func.now(),
                    },
                )
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def find_operador_by_nombre(self, nombre: str) -> Operador | None:
        target = _normalize(nombre)
        for operador in await self.list_operadores():
            if _normalize(operador.nombre) == target:
                return operador
        return None

    async def last_synced_at(self) -> datetime | None:
        stmt = select(func.max(CalendarEventModel.synced_at))
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def count_events(self) -> int:
        stmt = select(func.count()).select_from(CalendarEventModel)
        return (await self._session.execute(stmt)).scalar_one()


def _dedupe_by_gestion_id(events: list[CalendarEvent]) -> list[CalendarEvent]:
    seen: set[str] = set()
    deduped: list[CalendarEvent] = []
    for event in events:
        if event.id in seen:
            continue
        seen.add(event.id)
        deduped.append(event)
    return deduped


def _to_entity(model: CalendarEventModel) -> CalendarEvent:
    return CalendarEvent(
        id=model.gestion_event_id,
        title=model.title,
        start=model.start,
        operador_id=model.operador_id,
        all_day=model.all_day,
        background_color=model.background_color,
        border_color=model.border_color,
        type=model.type,
        tittle_tooltip=model.tittle_tooltip,
        content_tooltip=model.content_tooltip,
        string_tipo_evento=model.string_tipo_evento,
        cliente=model.cliente,
        vendedor=model.vendedor,
        fecha_entrega=model.fecha_entrega,
        fecha_entrega_deseada=model.fecha_entrega_deseada,
        sucursal_entrega=model.sucursal_entrega,
        sucursal_instalacion=model.sucursal_instalacion,
        sucursal_despacho=model.sucursal_despacho,
        contacto_entrega=model.contacto_entrega,
        contacto_instalacion=model.contacto_instalacion,
        bultos=model.bultos,
        costo_seguro=model.costo_seguro,
        costo_recambio=model.costo_recambio,
    )


def _to_model(event: CalendarEvent, operador_id: str) -> CalendarEventModel:
    return CalendarEventModel(
        id=uuid.uuid4(),
        gestion_event_id=event.id,
        operador_id=operador_id,
        event_date=date.fromisoformat(event.start[:10]),
        title=event.title,
        start=event.start,
        all_day=event.all_day,
        background_color=event.background_color,
        border_color=event.border_color,
        type=event.type,
        tittle_tooltip=event.tittle_tooltip,
        content_tooltip=event.content_tooltip,
        string_tipo_evento=event.string_tipo_evento,
        cliente=event.cliente,
        vendedor=event.vendedor,
        fecha_entrega=event.fecha_entrega,
        fecha_entrega_deseada=event.fecha_entrega_deseada,
        sucursal_entrega=event.sucursal_entrega,
        sucursal_instalacion=event.sucursal_instalacion,
        sucursal_despacho=event.sucursal_despacho,
        contacto_entrega=event.contacto_entrega,
        contacto_instalacion=event.contacto_instalacion,
        bultos=event.bultos,
        costo_seguro=event.costo_seguro,
        costo_recambio=event.costo_recambio,
    )
