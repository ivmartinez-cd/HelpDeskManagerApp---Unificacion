"""Tests unitarios de DownloadAndProcessFtpDb3UseCase.

Usan un stub de FtpDb3Downloader que escribe un DB3 real en disco — sin
conexión FTP real ni DB de Postgres.
"""
import os
import sqlite3
import uuid

import pytest

from src.modules.contadores.application.dtos.download_ftp_db3_request import DownloadFtpDb3Request
from src.modules.contadores.application.use_cases.download_and_process_ftp_db3 import (
    DownloadAndProcessFtpDb3UseCase,
)
from src.modules.contadores.application.use_cases.run_db3_export import RunDb3ExportUseCase
from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.domain.errors import FtpClientNotFoundError
from src.modules.contadores.infrastructure.csv.csv_db3_writer import CsvDb3Writer
from src.modules.contadores.infrastructure.sqlite.sqlite3_db3_file_reader import (
    Sqlite3Db3FileReader,
)

# ---------------------------------------------------------------------------
# Infraestructura de test
# ---------------------------------------------------------------------------


class InMemoryFtpClientRepository:
    def __init__(self, clients: list[FtpClient] | None = None) -> None:
        self._store: dict[uuid.UUID, FtpClient] = {c.id: c for c in (clients or [])}

    async def get_by_id(self, client_id: uuid.UUID) -> FtpClient | None:
        return self._store.get(client_id)

    async def get_by_name(self, name: str) -> FtpClient | None:
        return next((c for c in self._store.values() if c.name == name), None)

    async def list_all(self) -> list[FtpClient]:
        return sorted(self._store.values(), key=lambda c: c.name)

    async def add(self, client: FtpClient) -> None:
        self._store[client.id] = client

    async def save(self, client: FtpClient) -> None:
        self._store[client.id] = client

    async def delete(self, client_id: uuid.UUID) -> None:
        self._store.pop(client_id, None)


class StubFtpDb3Downloader:
    """Stub que escribe un DB3 sintético en dest_path y registra qué archivo
    'descargó'. Si `should_raise` es True, simula un error de red."""

    def __init__(self, *, should_raise: bool = False) -> None:
        self.should_raise = should_raise
        self.called_with: list[dict] = []

    def download(self, client: FtpClient, *, dest_path: str, timeout: int = 8) -> str:
        self.called_with.append({"client": client, "dest_path": dest_path, "timeout": timeout})
        if self.should_raise:
            raise ConnectionError("Simulated FTP error")
        _write_minimal_db3(dest_path)
        return dest_path


def _write_minimal_db3(path: str) -> None:
    """Escribe un SQLite3 mínimo válido para que RunDb3ExportUseCase lo procese."""
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE counters "
        "(serialnumber TEXT, readdate TEXT, readvalue INTEGER, model TEXT, counterclass_id INTEGER)"
    )
    conn.execute(
        "INSERT INTO counters VALUES ('SER001','2026-08-05 10:00:00',1000,'ModeloX',10)"
    )
    conn.commit()
    conn.close()


def _make_client() -> FtpClient:
    return FtpClient(
        id=uuid.uuid4(),
        name="ClientePrueba",
        host="ftp.test.com",
        user="u",
        password="p",
    )


def _make_use_case(
    client: FtpClient,
    stub: StubFtpDb3Downloader,
    output_dir: str,
) -> tuple[DownloadAndProcessFtpDb3UseCase, DownloadFtpDb3Request]:
    repo = InMemoryFtpClientRepository([client])
    db3_uc = RunDb3ExportUseCase(Sqlite3Db3FileReader(), CsvDb3Writer())
    uc = DownloadAndProcessFtpDb3UseCase(repo, stub, db3_uc)
    req = DownloadFtpDb3Request(client_id=str(client.id), output_dir=output_dir)
    return uc, req


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_raises_not_found_when_client_missing(tmp_path) -> None:
    repo = InMemoryFtpClientRepository()
    stub = StubFtpDb3Downloader()
    db3_uc = RunDb3ExportUseCase(Sqlite3Db3FileReader(), CsvDb3Writer())
    uc = DownloadAndProcessFtpDb3UseCase(repo, stub, db3_uc)
    req = DownloadFtpDb3Request(client_id=str(uuid.uuid4()), output_dir=str(tmp_path))

    with pytest.raises(FtpClientNotFoundError):
        await uc.execute(req)


async def test_generates_csv_from_ftp_download(tmp_path) -> None:
    client = _make_client()
    stub = StubFtpDb3Downloader()
    uc, req = _make_use_case(client, stub, str(tmp_path))

    result = await uc.execute(req)

    assert result.client_name == "ClientePrueba"
    assert result.row_count == 1
    assert result.csv_path.endswith(".csv")
    assert os.path.isfile(result.csv_path)


async def test_temp_db3_is_deleted_after_successful_process(tmp_path) -> None:
    client = _make_client()
    stub = StubFtpDb3Downloader()
    uc, req = _make_use_case(client, stub, str(tmp_path))

    await uc.execute(req)

    downloaded_path = stub.called_with[0]["dest_path"]
    assert not os.path.isfile(downloaded_path), "El temporal .db3 debe borrarse tras procesar"


async def test_temp_db3_is_deleted_even_when_ftp_download_fails(tmp_path) -> None:
    client = _make_client()
    stub = StubFtpDb3Downloader(should_raise=True)
    uc, req = _make_use_case(client, stub, str(tmp_path))

    with pytest.raises(ConnectionError):
        await uc.execute(req)

    downloaded_path = stub.called_with[0]["dest_path"]
    assert not os.path.isfile(downloaded_path), (
        "El temporal .db3 debe borrarse aunque falle la descarga"
    )


async def test_downloader_receives_correct_client(tmp_path) -> None:
    client = _make_client()
    stub = StubFtpDb3Downloader()
    uc, req = _make_use_case(client, stub, str(tmp_path))

    await uc.execute(req)

    assert len(stub.called_with) == 1
    assert stub.called_with[0]["client"].id == client.id
