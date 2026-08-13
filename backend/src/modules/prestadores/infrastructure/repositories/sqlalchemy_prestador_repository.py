import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.infrastructure.models.prestador_models import PrestadorModel


class SqlAlchemyPrestadorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prestador_id: uuid.UUID) -> Prestador | None:
        model = await self._session.get(PrestadorModel, prestador_id)
        return _to_prestador_entity(model) if model else None

    async def get_by_siges_empresa_id(self, siges_empresa_id: int) -> Prestador | None:
        stmt = select(PrestadorModel).where(
            PrestadorModel.siges_empresa_id == siges_empresa_id
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_prestador_entity(model) if model else None

    async def list_all(self, *, include_inactive: bool = False) -> list[Prestador]:
        stmt = select(PrestadorModel)
        if not include_inactive:
            stmt = stmt.where(PrestadorModel.is_active.is_(True))
        stmt = stmt.order_by(PrestadorModel.den_comercial)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_prestador_entity(r) for r in rows]

    async def add(self, prestador: Prestador) -> None:
        model = PrestadorModel(
            id=prestador.id,
            siges_empresa_id=prestador.siges_empresa_id,
            den_comercial=prestador.den_comercial,
            razon_social=prestador.razon_social,
            cuit=prestador.cuit,
            equipos=prestador.equipos,
            operador_id=prestador.operador_id,
            is_active=prestador.is_active,
        )
        self._session.add(model)
        await self._session.flush()

    async def save(self, prestador: Prestador) -> None:
        model = await self._session.get(PrestadorModel, prestador.id)
        if model:
            model.den_comercial = prestador.den_comercial
            model.razon_social = prestador.razon_social
            model.cuit = prestador.cuit
            model.equipos = prestador.equipos
            model.operador_id = prestador.operador_id
            model.is_active = prestador.is_active
            await self._session.flush()


def _to_prestador_entity(model: PrestadorModel) -> Prestador:
    return Prestador(
        id=model.id,
        siges_empresa_id=model.siges_empresa_id,
        den_comercial=model.den_comercial,
        razon_social=model.razon_social,
        cuit=model.cuit,
        equipos=model.equipos,
        operador_id=model.operador_id,
        is_active=model.is_active,
    )
