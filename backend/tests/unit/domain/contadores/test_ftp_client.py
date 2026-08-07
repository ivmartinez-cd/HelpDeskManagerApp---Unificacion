import uuid

from src.modules.contadores.domain.entities.ftp_client import (
    DEFAULT_PATH,
    DEFAULT_PATTERN,
    FtpClient,
)


def _build_client(client_id: uuid.UUID, name: str = "ClienteA") -> FtpClient:
    return FtpClient(id=client_id, name=name, host="ftp.cliente.com", user="u", password="p")


def test_equality_is_based_on_identity_not_on_field_values() -> None:
    shared_id = uuid.uuid4()
    same_identity = _build_client(shared_id, "ClienteA")
    same_identity_different_fields = _build_client(shared_id, "ClienteB")
    different_identity = _build_client(uuid.uuid4(), "ClienteA")

    assert same_identity == same_identity_different_fields
    assert same_identity != different_identity


def test_defaults_match_the_legacy_app_behavior() -> None:
    client = _build_client(uuid.uuid4())

    assert client.path == DEFAULT_PATH == "/"
    assert client.pattern == DEFAULT_PATTERN == "PrinterMonitorClient.db3.*"
