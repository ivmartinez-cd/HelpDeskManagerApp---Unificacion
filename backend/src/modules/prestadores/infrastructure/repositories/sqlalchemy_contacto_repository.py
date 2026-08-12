import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.infrastructure.models.prestador_models import (
    PrestadorContactoModel,
)


class SqlAlchemyContactoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, contacto_id: uuid.UUID) -> ContactoPrestador | None:
        model = await self._session.get(PrestadorContactoModel, contacto_id)
        return _to_contacto_entity(model) if model else None

    async def list_by_prestador(self, prestador_id: uuid.UUID) -> list[ContactoPrestador]:
        stmt = (
            select(PrestadorContactoModel)
            .where(PrestadorContactoModel.prestador_id == prestador_id)
            .order_by(PrestadorContactoModel.sort_order)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_contacto_entity(r) for r in rows]

    async def list_by_prestadores(
        self, prestador_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[ContactoPrestador]]:
        if not prestador_ids:
            return {}
        stmt = (
            select(PrestadorContactoModel)
            .where(PrestadorContactoModel.prestador_id.in_(prestador_ids))
            .order_by(PrestadorContactoModel.sort_order)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        grouped: dict[uuid.UUID, list[ContactoPrestador]] = {}
        for r in rows:
            grouped.setdefault(r.prestador_id, []).append(_to_contacto_entity(r))
        return grouped

    async def add(self, contacto: ContactoPrestador) -> None:
        model = PrestadorContactoModel(
            id=contacto.id,
            prestador_id=contacto.prestador_id,
            nombre=contacto.nombre,
            telefono=contacto.telefono,
            email=contacto.email,
            is_principal=contacto.is_principal,
            sort_order=contacto.sort_order,
        )
        self._session.add(model)
        await self._session.flush()

    async def save(self, contacto: ContactoPrestador) -> None:
        model = await self._session.get(PrestadorContactoModel, contacto.id)
        if model:
            model.nombre = contacto.nombre
            model.telefono = contacto.telefono
            model.email = contacto.email
            model.is_principal = contacto.is_principal
            model.sort_order = contacto.sort_order
            await self._session.flush()

    async def delete(self, contacto_id: uuid.UUID) -> None:
        stmt = delete(PrestadorContactoModel).where(PrestadorContactoModel.id == contacto_id)
        await self._session.execute(stmt)
        await self._session.flush()


def _to_contacto_entity(model: PrestadorContactoModel) -> ContactoPrestador:
    return ContactoPrestador(
        id=model.id,
        prestador_id=model.prestador_id,
        nombre=model.nombre,
        telefono=model.telefono,
        email=model.email,
        is_principal=model.is_principal,
        sort_order=model.sort_order,
    )
