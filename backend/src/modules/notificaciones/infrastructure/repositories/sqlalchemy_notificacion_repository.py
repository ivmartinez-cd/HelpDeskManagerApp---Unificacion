import uuid
from datetime import datetime

from sqlalchemy import ColumnElement, Select, and_, exists, func, literal, select, true
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.notificaciones.domain.entities.notificacion import (
    Notificacion,
    NuevaNotificacion,
)
from src.modules.notificaciones.domain.repositories.notificacion_repository import Audiencias
from src.modules.notificaciones.infrastructure.models.notificacion_model import (
    NotificacionLecturaModel as L,
)
from src.modules.notificaciones.infrastructure.models.notificacion_model import (
    NotificacionModel as N,
)


def _visible(audiencias: Audiencias) -> ColumnElement[bool]:
    return true() if audiencias is None else N.audiencia.in_(audiencias)


def _leida(usuario_id: uuid.UUID) -> ColumnElement[bool]:
    return exists().where(and_(L.notificacion_id == N.id, L.usuario_id == usuario_id))


def _pagina(
    filtro: ColumnElement[bool], leida: ColumnElement[bool], offset: int, limit: int
) -> Select[tuple[uuid.UUID, str, str, str | None, datetime, bool]]:
    return (
        select(N.id, N.titulo, N.cuerpo, N.url, N.creada_en, leida.label("leida"))
        .where(filtro)
        .order_by(N.creada_en.desc(), N.id)
        .offset(offset)
        .limit(limit)
    )


class SqlAlchemyNotificacionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def publicar(self, notificaciones: list[NuevaNotificacion]) -> None:
        if not notificaciones:
            return
        valores = [
            {
                "clave": n.clave,
                "audiencia": n.audiencia,
                "titulo": n.titulo,
                "cuerpo": n.cuerpo,
                "url": n.url,
            }
            for n in notificaciones
        ]
        stmt = insert(N).values(valores).on_conflict_do_nothing(index_elements=[N.clave])
        await self._session.execute(stmt)

    async def listar(
        self,
        usuario_id: uuid.UUID,
        audiencias: Audiencias,
        *,
        solo_no_leidas: bool,
        offset: int,
        limit: int,
    ) -> tuple[list[Notificacion], int]:
        leida = _leida(usuario_id)
        filtro = _visible(audiencias)
        if solo_no_leidas:
            filtro = and_(filtro, ~leida)
        total = await self._session.scalar(select(func.count()).select_from(N).where(filtro))
        filas = await self._session.execute(_pagina(filtro, leida, offset, limit))
        items = [Notificacion(r.id, r.titulo, r.cuerpo, r.url, r.creada_en, r.leida) for r in filas]
        return items, total or 0

    async def marcar_leidas(
        self, usuario_id: uuid.UUID, audiencias: Audiencias, ids: list[uuid.UUID] | None
    ) -> int:
        filtro = and_(_visible(audiencias), ~_leida(usuario_id))
        if ids is not None:
            filtro = and_(filtro, N.id.in_(ids))
        origen = select(N.id, literal(usuario_id, UUID(as_uuid=True))).where(filtro)
        stmt = (
            insert(L)
            .from_select([L.notificacion_id, L.usuario_id], origen)
            .on_conflict_do_nothing()
        )
        resultado = await self._session.execute(stmt)
        return int(getattr(resultado, "rowcount", 0) or 0)
