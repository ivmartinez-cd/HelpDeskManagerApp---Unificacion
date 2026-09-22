"""Login + token del wsAyC securitizado (sep-2026) en el provider compartido."""

import json
from typing import Any

import pytest
from zeep.exceptions import Fault

from src.shared.domain.errors import ExternalPermissionDeniedError
from src.shared.infrastructure.wsayc import auth
from src.shared.infrastructure.wsayc.auth import WsAycAuthError, extract_token
from src.shared.infrastructure.wsayc.client_provider import WsAycClientProvider

# Respuestas reales del servidor (capturadas en el legacy SDSInsumos).
_LOGIN_ERROR = (
    '{"status":"ERROR","message":"Credenciales invalidas o el usuario no esta autorizado '
    'para servicios web (id_tipo = 11)."}'
)
_AUTH_FAULT = "SOAP-ENV:Client.AuthenticationError"
_ACL_FAULT = "SOAP-ENV:Client.AuthorizationError"


class FakeServer:
    def __init__(self, login_responses: list[str]) -> None:
        self.login_responses = login_responses
        self.logins = 0
        self.valid_token = "tok-1"
        self.denied: set[str] = set()
        self.calls: list[tuple[str, str | None]] = []

    def service(self, token: str | None) -> Any:
        server = self

        class _Service:
            def login(self, username: str, password: str) -> str:
                server.logins += 1
                return server.login_responses[min(server.logins, len(server.login_responses)) - 1]

            def getSupplyById(self, id: str) -> str:  # noqa: N802 — nombre del WSDL
                return server.handle("getSupplyById", token, id)

            def voidSupply(self, Datos: str) -> str:  # noqa: N802, N803 — nombres del WSDL
                return server.handle("voidSupply", token, Datos)

        return _Service()

    def handle(self, operation: str, token: str | None, arg: str) -> str:
        self.calls.append((operation, token))
        if token != self.valid_token:
            raise Fault("Token de autenticacion invalido o expirado.", code=_AUTH_FAULT)
        if operation in self.denied:
            raise Fault("Usuario no autorizado para el metodo.", code=_ACL_FAULT)
        return json.dumps({"ok": arg})


def _provider(server: FakeServer, credentials: tuple[str, str] = ("user", "pass")) -> Any:
    provider = WsAycClientProvider("https://x?wsdl", "https://x", 30.0, credentials)
    provider._raw_service = server.service  # type: ignore[method-assign]
    return provider


def test_primera_llamada_hace_login_y_reutiliza_el_token() -> None:
    server = FakeServer(['{"status":"OK","token":"tok-1"}'])
    provider = _provider(server)
    assert provider.service().getSupplyById(id="1") == '{"ok": "1"}'
    provider.service().getSupplyById(id="2")
    assert server.logins == 1
    assert server.calls == [("getSupplyById", "tok-1"), ("getSupplyById", "tok-1")]


def test_token_vencido_relogin_una_vez_y_repite() -> None:
    server = FakeServer(['{"status":"OK","token":"tok-1"}', '{"status":"OK","token":"tok-2"}'])
    provider = _provider(server)
    provider.service().getSupplyById(id="1")
    server.valid_token = "tok-2"  # venció el de 8 h
    assert provider.service().voidSupply(Datos="x") == '{"ok": "x"}'
    assert server.logins == 2
    assert server.calls[-2:] == [("voidSupply", "tok-1"), ("voidSupply", "tok-2")]


def test_acl_sin_el_metodo_da_error_de_permisos_sin_relogin() -> None:
    server = FakeServer(['{"status":"OK","token":"tok-1"}'])
    server.denied.add("voidSupply")
    provider = _provider(server)
    with pytest.raises(ExternalPermissionDeniedError) as info:
        provider.service().voidSupply(Datos="x")
    assert info.value.message == ExternalPermissionDeniedError.user_message
    assert server.logins == 1


def test_login_rechazado_no_se_reintenta_durante_el_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = FakeServer([_LOGIN_ERROR])
    provider = _provider(server)
    for _ in range(3):
        with pytest.raises(WsAycAuthError, match="Credenciales invalidas"):
            provider.service().getSupplyById(id="1")
    assert server.logins == 1
    monkeypatch.setattr(auth, "_LOGIN_COOLDOWN_SECONDS", 0.0)
    with pytest.raises(WsAycAuthError):
        provider.service().getSupplyById(id="1")
    assert server.logins == 2


def test_sin_credenciales_falla_claro_sin_llamar_al_login() -> None:
    server = FakeServer(['{"status":"OK","token":"tok-1"}'])
    with pytest.raises(WsAycAuthError, match="WSAYC_USERNAME"):
        _provider(server, ("", "")).service().getSupplyById(id="1")
    assert server.logins == 0


@pytest.mark.parametrize(
    "raw",
    ['{"status":"OK","token":"t"}', '{"data":{"token":"t"}}', '{"Respuesta":{"jwt":"t"}}'],
)
def test_extract_token_formatos(raw: str) -> None:
    assert extract_token(raw) == "t"


def test_extract_token_sin_token_no_filtra_la_respuesta() -> None:
    with pytest.raises(WsAycAuthError, match=r"keys: \['otro', 'status'\]"):
        extract_token('{"status":"OK","otro":"secreto"}')
