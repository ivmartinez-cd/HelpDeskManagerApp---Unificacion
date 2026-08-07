import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.infrastructure.models.ftp_client_model import FtpClientModel


class SqlAlchemyFtpClientRepository:
    """Implementa el puerto FtpClientRepository. `add`/`save`/`delete` hacen
    `flush`, no `commit` — igual convención que el resto del monolito (ver
    SqlAlchemyUserRepository)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, client_id: uuid.UUID) -> FtpClient | None:
        model = await self._session.get(FtpClientModel, client_id)
        return _to_entity(model) if model else None

    async def get_by_name(self, name: str) -> FtpClient | None:
        stmt = select(FtpClientModel).where(FtpClientModel.name == name)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_all(self) -> list[FtpClient]:
        stmt = select(FtpClientModel).order_by(FtpClientModel.name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def add(self, client: FtpClient) -> None:
        self._session.add(_to_new_model(client))
        await self._session.flush()

    async def save(self, client: FtpClient) -> None:
        model = await self._session.get(FtpClientModel, client.id)
        if model is None:
            raise LookupError(f"FtpClient {client.id} no existe")
        _apply_changes(model, client)
        await self._session.flush()

    async def delete(self, client_id: uuid.UUID) -> None:
        model = await self._session.get(FtpClientModel, client_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()


def _to_entity(model: FtpClientModel) -> FtpClient:
    return FtpClient(
        id=model.id,
        name=model.name,
        host=model.host,
        user=model.user,
        password=model.password,
        path=model.path,
        pattern=model.pattern,
    )


def _to_new_model(client: FtpClient) -> FtpClientModel:
    return FtpClientModel(
        id=client.id,
        name=client.name,
        host=client.host,
        user=client.user,
        password=client.password,
        path=client.path,
        pattern=client.pattern,
    )


def _apply_changes(model: FtpClientModel, client: FtpClient) -> None:
    model.name = client.name
    model.host = client.host
    model.user = client.user
    model.password = client.password
    model.path = client.path
    model.pattern = client.pattern
