import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.entities.cliente_nuevo import ESTADOS_ABIERTOS, ClienteNuevo
from src.modules.contadores.infrastructure.models.cliente_nuevo_model import ClienteNuevoModel

_CAMPOS_EDITABLES = (
    "cliente",
    "siges_empresa_id",
    "contrato_nro",
    "fecha_firma",
    "vendedor",
    "operador_id",
    "implementacion_servicio",
    "fecha_estimada_implementacion",
    "fecha_estimada_primera_facturacion",
    "dia_corte",
    "equipos_previstos",
    "estado",
    "stc_enviado_el",
    "notas",
)


class SqlAlchemyClienteNuevoRepository:
    """Implementa `ClienteNuevoRepository`. `add`/`save`/`delete` hacen
    `flush`, no `commit` — misma convención que el resto del monolito."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, ficha_id: uuid.UUID) -> ClienteNuevo | None:
        model = await self._session.get(ClienteNuevoModel, ficha_id)
        return _to_entity(model) if model else None

    async def get_abierta_by_cliente(self, cliente: str) -> ClienteNuevo | None:
        stmt = (
            select(ClienteNuevoModel)
            .where(ClienteNuevoModel.cliente.ilike(cliente.strip()))
            .where(ClienteNuevoModel.estado.in_(ESTADOS_ABIERTOS))
            .limit(1)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_all(self) -> list[ClienteNuevo]:
        stmt = select(ClienteNuevoModel).order_by(
            ClienteNuevoModel.created_at.desc(), ClienteNuevoModel.cliente
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def list_siges_empresa_ids(self) -> set[int]:
        stmt = select(ClienteNuevoModel.siges_empresa_id).where(
            ClienteNuevoModel.siges_empresa_id.is_not(None)
        )
        return {row for row in (await self._session.execute(stmt)).scalars().all() if row}

    async def add(self, ficha: ClienteNuevo) -> None:
        self._session.add(_to_new_model(ficha))
        await self._session.flush()

    async def save(self, ficha: ClienteNuevo) -> None:
        model = await self._session.get(ClienteNuevoModel, ficha.id)
        if model is None:
            raise LookupError(f"ClienteNuevo {ficha.id} no existe")
        for campo in _CAMPOS_EDITABLES:
            setattr(model, campo, getattr(ficha, campo))
        # La marca la pone el caso de uso, así la respuesta y la fila coinciden.
        model.updated_at = ficha.updated_at
        await self._session.flush()

    async def delete(self, ficha_id: uuid.UUID) -> None:
        model = await self._session.get(ClienteNuevoModel, ficha_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()


def _to_entity(model: ClienteNuevoModel) -> ClienteNuevo:
    return ClienteNuevo(
        id=model.id,
        cliente=model.cliente,
        created_by_user_id=model.created_by_user_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        **{campo: getattr(model, campo) for campo in _CAMPOS_EDITABLES if campo != "cliente"},
    )


def _to_new_model(ficha: ClienteNuevo) -> ClienteNuevoModel:
    return ClienteNuevoModel(
        id=ficha.id,
        created_by_user_id=ficha.created_by_user_id,
        created_at=ficha.created_at,
        updated_at=ficha.updated_at,
        **{campo: getattr(ficha, campo) for campo in _CAMPOS_EDITABLES},
    )
