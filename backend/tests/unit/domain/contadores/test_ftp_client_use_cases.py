"""Tests unitarios de los use cases de CRUD de FtpClient.

Usan un repositorio en memoria — sin DB, sin red, sin I/O.
"""
import uuid

import pytest

from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientRequest
from src.modules.contadores.application.use_cases.create_ftp_client import CreateFtpClientUseCase
from src.modules.contadores.application.use_cases.delete_ftp_client import DeleteFtpClientUseCase
from src.modules.contadores.application.use_cases.get_ftp_client import GetFtpClientUseCase
from src.modules.contadores.application.use_cases.list_ftp_clients import ListFtpClientsUseCase
from src.modules.contadores.application.use_cases.update_ftp_client import UpdateFtpClientUseCase
from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.domain.errors import (
    DuplicateFtpClientNameError,
    FtpClientNotFoundError,
)

# ---------------------------------------------------------------------------
# Repo en memoria
# ---------------------------------------------------------------------------


class InMemoryFtpClientRepository:
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, FtpClient] = {}

    async def get_by_id(self, client_id: uuid.UUID) -> FtpClient | None:
        return self._store.get(client_id)

    async def get_by_name(self, name: str) -> FtpClient | None:
        return next((c for c in self._store.values() if c.name == name), None)

    async def list_all(self) -> list[FtpClient]:
        return sorted(self._store.values(), key=lambda c: c.name)

    async def add(self, client: FtpClient) -> None:
        self._store[client.id] = client

    async def save(self, client: FtpClient) -> None:
        if client.id not in self._store:
            raise LookupError(f"FtpClient {client.id} no existe")
        self._store[client.id] = client

    async def delete(self, client_id: uuid.UUID) -> None:
        self._store.pop(client_id, None)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


def _build_request(name: str = "ClienteA") -> FtpClientRequest:
    return FtpClientRequest(name=name, host="ftp.test.com", user="u", password="p")


# ---------------------------------------------------------------------------
# ListFtpClientsUseCase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_returns_empty_when_no_clients() -> None:
    repo = InMemoryFtpClientRepository()

    results = await ListFtpClientsUseCase(repo).execute()

    assert results == []


@pytest.mark.asyncio
async def test_list_returns_clients_ordered_by_name() -> None:
    repo = InMemoryFtpClientRepository()
    await repo.add(FtpClient(id=uuid.uuid4(), name="Zeta", host="h", user="u", password="p"))
    await repo.add(FtpClient(id=uuid.uuid4(), name="Alfa", host="h", user="u", password="p"))

    results = await ListFtpClientsUseCase(repo).execute()

    assert [r.name for r in results] == ["Alfa", "Zeta"]


# ---------------------------------------------------------------------------
# GetFtpClientUseCase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_raises_not_found_for_unknown_id() -> None:
    repo = InMemoryFtpClientRepository()

    with pytest.raises(FtpClientNotFoundError):
        await GetFtpClientUseCase(repo).execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_get_returns_client_by_id() -> None:
    repo = InMemoryFtpClientRepository()
    client_id = uuid.uuid4()
    await repo.add(FtpClient(id=client_id, name="X", host="h", user="u", password="p"))

    result = await GetFtpClientUseCase(repo).execute(client_id)

    assert result.id == str(client_id)
    assert result.name == "X"


# ---------------------------------------------------------------------------
# CreateFtpClientUseCase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_adds_client_and_returns_result() -> None:
    repo = InMemoryFtpClientRepository()

    result = await CreateFtpClientUseCase(repo).execute(_build_request("Nuevo"))

    assert result.name == "Nuevo"
    assert result.id  # UUID asignado
    clients = await repo.list_all()
    assert len(clients) == 1


@pytest.mark.asyncio
async def test_create_raises_duplicate_error_when_name_exists() -> None:
    repo = InMemoryFtpClientRepository()
    await CreateFtpClientUseCase(repo).execute(_build_request("Existente"))

    with pytest.raises(DuplicateFtpClientNameError):
        await CreateFtpClientUseCase(repo).execute(_build_request("Existente"))


@pytest.mark.asyncio
async def test_create_does_not_expose_password_in_result() -> None:
    repo = InMemoryFtpClientRepository()

    result = await CreateFtpClientUseCase(repo).execute(_build_request())

    assert not hasattr(result, "password")


# ---------------------------------------------------------------------------
# UpdateFtpClientUseCase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_raises_not_found_for_unknown_id() -> None:
    repo = InMemoryFtpClientRepository()

    with pytest.raises(FtpClientNotFoundError):
        await UpdateFtpClientUseCase(repo).execute(uuid.uuid4(), _build_request())


@pytest.mark.asyncio
async def test_update_persists_new_host() -> None:
    repo = InMemoryFtpClientRepository()
    result = await CreateFtpClientUseCase(repo).execute(_build_request("Original"))
    client_id = uuid.UUID(result.id)
    updated_request = FtpClientRequest(
        name="Original", host="nuevo.host.com", user="u2", password="p2"
    )

    updated = await UpdateFtpClientUseCase(repo).execute(client_id, updated_request)

    assert updated.host == "nuevo.host.com"
    assert updated.user == "u2"


# ---------------------------------------------------------------------------
# DeleteFtpClientUseCase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_raises_not_found_for_unknown_id() -> None:
    repo = InMemoryFtpClientRepository()

    with pytest.raises(FtpClientNotFoundError):
        await DeleteFtpClientUseCase(repo).execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_delete_removes_client_from_repo() -> None:
    repo = InMemoryFtpClientRepository()
    result = await CreateFtpClientUseCase(repo).execute(_build_request())
    client_id = uuid.UUID(result.id)

    await DeleteFtpClientUseCase(repo).execute(client_id)

    assert await repo.get_by_id(client_id) is None
