"""Refresh de token ERS con transporte mockeado."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from src.modules.contadores.infrastructure.ers.httpx_ers_token_refresher import refresh_ers_token
from src.shared.domain.errors import ExternalServiceError
from tests.unit.infrastructure.contadores.settings_stub import make_settings


def _patch_transport(
    monkeypatch: pytest.MonkeyPatch, handler: Any
) -> None:
    """Reemplaza httpx.AsyncClient por uno con MockTransport, preservando el
    resto de los kwargs (cookies, follow_redirects) del call site real."""
    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("timeout", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


async def test_refresh_ers_token_persiste_el_bearer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "auth-api.cp.epson.com"
        return httpx.Response(200, json={"access_token": "abc"})

    _patch_transport(monkeypatch, handler)
    token_file = tmp_path / "sub" / "token.json"

    data = await refresh_ers_token(str(token_file), settings=make_settings())

    assert data["token"] == "Bearer abc"
    persistido = json.loads(token_file.read_text(encoding="utf-8"))
    assert persistido["token"] == "Bearer abc"
    assert persistido["username"] == "ers@test.local"


async def test_refresh_ers_token_sin_credenciales(tmp_path: Path) -> None:
    with pytest.raises(ExternalServiceError, match="credenciales"):
        await refresh_ers_token(
            str(tmp_path / "t.json"), settings=make_settings(epson_ers_username="")
        )


async def test_refresh_ers_token_login_rechazado(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(401, json={}))
    with pytest.raises(ExternalServiceError, match="401"):
        await refresh_ers_token(str(tmp_path / "t.json"), settings=make_settings())


async def test_refresh_ers_token_respuesta_sin_access_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={}))
    with pytest.raises(ExternalServiceError, match="access_token"):
        await refresh_ers_token(str(tmp_path / "t.json"), settings=make_settings())


async def test_refresh_ers_token_error_de_conexion_se_envuelve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def explota(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    _patch_transport(monkeypatch, explota)
    with pytest.raises(ExternalServiceError, match="conectar"):
        await refresh_ers_token(str(tmp_path / "t.json"), settings=make_settings())
