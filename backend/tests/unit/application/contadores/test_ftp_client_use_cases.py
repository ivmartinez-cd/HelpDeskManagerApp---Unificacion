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
    FtpGrupoEconomicoRequeridoError,
    GrupoEconomicoSinFtpError,
)
from src.modules.contadores.domain.repositories.grupos_economicos_ftp_gateway import (
    CredencialesFtp,
    GrupoEconomicoFtp,
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


class FakeGrupos:
    """Siges en memoria: grupo económico → usuario/contraseña FTP."""

    def __init__(self) -> None:
        self.credenciales_por_grupo = {_GRUPO: CredencialesFtp("acme", "secreta")}

    async def listar(self) -> list[GrupoEconomicoFtp]:
        return [
            GrupoEconomicoFtp(i, "Acme", c.usuario) for i, c in self.credenciales_por_grupo.items()
        ]

    async def credenciales(self, grupo_id: int) -> CredencialesFtp | None:
        return self.credenciales_por_grupo.get(grupo_id)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

_GRUPO = 7
_HOST = "ftp.empresa.com"


def _build_request(name: str = "ClienteA", grupo: int | None = _GRUPO) -> FtpClientRequest:
    return FtpClientRequest(name=name, grupo_economico_id=grupo)


def _create(repo: InMemoryFtpClientRepository) -> CreateFtpClientUseCase:
    return CreateFtpClientUseCase(repo, FakeGrupos(), _HOST)


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

    result = await _create(repo).execute(_build_request("Nuevo"))

    assert result.name == "Nuevo"
    assert result.id  # UUID asignado
    clients = await repo.list_all()
    assert len(clients) == 1


@pytest.mark.asyncio
async def test_create_raises_duplicate_error_when_name_exists() -> None:
    repo = InMemoryFtpClientRepository()
    await _create(repo).execute(_build_request("Existente"))

    with pytest.raises(DuplicateFtpClientNameError):
        await _create(repo).execute(_build_request("Existente"))


@pytest.mark.asyncio
async def test_create_toma_usuario_de_siges_y_no_guarda_contrasena() -> None:
    repo = InMemoryFtpClientRepository()

    result = await _create(repo).execute(_build_request())

    guardado = await repo.get_by_id(uuid.UUID(result.id))
    assert guardado is not None
    assert (guardado.host, guardado.user, guardado.password) == (_HOST, "acme", None)
    assert guardado.grupo_economico_id == _GRUPO


@pytest.mark.asyncio
async def test_create_sin_grupo_o_con_grupo_sin_ftp_se_rechaza() -> None:
    repo = InMemoryFtpClientRepository()

    with pytest.raises(FtpGrupoEconomicoRequeridoError):
        await _create(repo).execute(_build_request(grupo=None))
    with pytest.raises(GrupoEconomicoSinFtpError):
        await _create(repo).execute(_build_request(grupo=999))
    assert await repo.list_all() == []


@pytest.mark.asyncio
async def test_create_does_not_expose_password_in_result() -> None:
    repo = InMemoryFtpClientRepository()

    result = await _create(repo).execute(_build_request())

    assert not hasattr(result, "password")


# ---------------------------------------------------------------------------
# UpdateFtpClientUseCase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_raises_not_found_for_unknown_id() -> None:
    repo = InMemoryFtpClientRepository()

    with pytest.raises(FtpClientNotFoundError):
        await UpdateFtpClientUseCase(repo, FakeGrupos()).execute(uuid.uuid4(), _build_request())


def _cliente_local() -> FtpClient:
    return FtpClient(
        id=uuid.uuid4(), name="Viejo", host="ftp.cliente.com", user="u", password="local"
    )


@pytest.mark.asyncio
async def test_update_no_permite_cambiar_servidor_usuario_ni_contrasena() -> None:
    repo = InMemoryFtpClientRepository()
    client = _cliente_local()
    await repo.add(client)
    request = FtpClientRequest(name="Renombrado", grupo_economico_id=None, path="/db3")

    updated = await UpdateFtpClientUseCase(repo, FakeGrupos()).execute(client.id, request)

    guardado = await repo.get_by_id(client.id)
    assert guardado is not None
    assert (updated.name, updated.path) == ("Renombrado", "/db3")
    assert (guardado.host, guardado.user, guardado.password) == ("ftp.cliente.com", "u", "local")


@pytest.mark.asyncio
async def test_update_vincular_grupo_pasa_a_siges_y_descarta_la_contrasena_local() -> None:
    repo = InMemoryFtpClientRepository()
    client = _cliente_local()
    await repo.add(client)

    await UpdateFtpClientUseCase(repo, FakeGrupos()).execute(client.id, _build_request("Viejo"))

    guardado = await repo.get_by_id(client.id)
    assert guardado is not None
    assert (guardado.user, guardado.password, guardado.grupo_economico_id) == ("acme", None, _GRUPO)
    assert guardado.host == "ftp.cliente.com"


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
    result = await _create(repo).execute(_build_request())
    client_id = uuid.UUID(result.id)

    await DeleteFtpClientUseCase(repo).execute(client_id)

    assert await repo.get_by_id(client_id) is None
