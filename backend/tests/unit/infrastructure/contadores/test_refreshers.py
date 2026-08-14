"""Refresh de token ERS y de sesión Gestión con transporte mockeado."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from src.modules.contadores.infrastructure.ers.httpx_ers_token_refresher import refresh_ers_token
from src.modules.contadores.infrastructure.gestion.gestion_session_refresher import (
    refresh_gestion_session,
)
from src.shared.domain.errors import ExternalServiceError
from tests.unit.infrastructure.contadores.settings_stub import make_settings

_LOGIN_HTML = '<form><input name="_csrf_token" value="csrf-123"/></form>'


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


def _gestion_handler_ok(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/login":
        return httpx.Response(200, text=_LOGIN_HTML)
    assert request.url.path == "/login_check"
    assert b"_csrf_token=csrf-123" in request.content
    return httpx.Response(302, headers={"set-cookie": "PHPSESSID=sess-1; Path=/"})


async def test_refresh_gestion_session_persiste_el_phpsessid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, _gestion_handler_ok)
    session_file = tmp_path / "gestion.json"

    data = await refresh_gestion_session(str(session_file), settings=make_settings())

    assert data["cookie"] == "theme=dark; PHPSESSID=sess-1"
    persistido = json.loads(session_file.read_text(encoding="utf-8"))
    assert persistido["username"] == "gestion-user"


async def test_refresh_gestion_session_sin_credenciales(tmp_path: Path) -> None:
    with pytest.raises(ExternalServiceError, match="credenciales"):
        await refresh_gestion_session(
            str(tmp_path / "g.json"), settings=make_settings(gestion_web_username="")
        )


async def test_refresh_gestion_session_sin_csrf_en_el_form(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, text="<form></form>"))
    with pytest.raises(ExternalServiceError, match="_csrf_token"):
        await refresh_gestion_session(str(tmp_path / "g.json"), settings=make_settings())


async def test_refresh_gestion_session_login_rechazado(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/login":
            return httpx.Response(200, text=_LOGIN_HTML)
        return httpx.Response(200, text="credenciales invalidas")  # sin redirect ni cookie

    _patch_transport(monkeypatch, handler)
    with pytest.raises(ExternalServiceError, match="Fallo el login"):
        await refresh_gestion_session(str(tmp_path / "g.json"), settings=make_settings())


async def test_refresh_gestion_session_error_de_conexion_se_envuelve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def explota(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    _patch_transport(monkeypatch, explota)
    with pytest.raises(ExternalServiceError, match="conectar"):
        await refresh_gestion_session(str(tmp_path / "g.json"), settings=make_settings())
