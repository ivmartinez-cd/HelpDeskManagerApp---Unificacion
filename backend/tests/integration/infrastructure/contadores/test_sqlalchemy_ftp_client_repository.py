import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.infrastructure.repositories.sqlalchemy_ftp_client_repository import (
    SqlAlchemyFtpClientRepository,
)


def _build_client(name: str = "ClienteA") -> FtpClient:
    return FtpClient(id=uuid.uuid4(), name=name, host="ftp.cliente.com", user="u", password="p")


async def test_add_then_get_by_id_round_trips(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFtpClientRepository(db_session)
    client = _build_client()

    await repo.add(client)
    found = await repo.get_by_id(client.id)

    assert found is not None
    assert found.name == "ClienteA"
    assert found.path == "/"
    assert found.pattern == "PrinterMonitorClient.db3.*"


async def test_get_by_name_finds_the_right_client(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFtpClientRepository(db_session)
    await repo.add(_build_client("Uno"))
    await repo.add(_build_client("Dos"))

    found = await repo.get_by_name("Dos")

    assert found is not None
    assert found.name == "Dos"


async def test_get_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFtpClientRepository(db_session)

    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_list_all_orders_by_name(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFtpClientRepository(db_session)
    await repo.add(_build_client("Zeta"))
    await repo.add(_build_client("Alfa"))

    clients = await repo.list_all()

    assert [c.name for c in clients] == ["Alfa", "Zeta"]


async def test_save_persists_changes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFtpClientRepository(db_session)
    client = _build_client()
    await repo.add(client)

    client.host = "otro-host.com"
    await repo.save(client)

    found = await repo.get_by_id(client.id)
    assert found is not None
    assert found.host == "otro-host.com"


async def test_delete_removes_the_client(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFtpClientRepository(db_session)
    client = _build_client()
    await repo.add(client)

    await repo.delete(client.id)

    assert await repo.get_by_id(client.id) is None
