"""ArgentinaDatosFeriadosClient: parseo tolerante de la respuesta y traducción
de fallos HTTP a ExternalServiceError. Sin red: httpx.MockTransport."""

import types
from collections.abc import Callable
from datetime import date
from typing import Any

import httpx
import pytest

from src.modules.vacaciones.infrastructure import argentinadatos_feriados_client as modulo
from src.modules.vacaciones.infrastructure.argentinadatos_feriados_client import (
    ArgentinaDatosFeriadosClient,
)
from src.shared.domain.errors import ExternalServiceError

Handler = Callable[[httpx.Request], httpx.Response]


def _con_transport(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> None:
    """El cliente instancia `httpx.AsyncClient` adentro; se le inyecta un
    MockTransport reemplazando el módulo `httpx` que ve, sin tocar httpx global."""
    transport = httpx.MockTransport(handler)

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, **kwargs)

    monkeypatch.setattr(
        modulo, "httpx", types.SimpleNamespace(AsyncClient=factory, HTTPError=httpx.HTTPError)
    )


async def test_fetch_parsea_feriados_e_ignora_items_invalidos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(
            200,
            json=[
                {"fecha": "2026-01-01", "tipo": "inamovible", "nombre": "Año Nuevo"},
                {"fecha": "no-es-fecha", "nombre": "Roto"},
                {"nombre": "Sin fecha"},
                "basura",
                {"fecha": "2026-03-24", "nombre": "Día de la Memoria"},
            ],
        )

    _con_transport(monkeypatch, handler)
    feriados = await ArgentinaDatosFeriadosClient().fetch(2026)

    assert urls == ["https://api.argentinadatos.com/v1/feriados/2026"]
    assert [(f.fecha, f.nombre) for f in feriados] == [
        (date(2026, 1, 1), "Año Nuevo"),
        (date(2026, 3, 24), "Día de la Memoria"),
    ]


async def test_fetch_con_error_http_levanta_external_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _con_transport(monkeypatch, lambda request: httpx.Response(503, text="down"))

    with pytest.raises(ExternalServiceError, match="2026"):
        await ArgentinaDatosFeriadosClient().fetch(2026)


async def test_fetch_con_error_de_conexion_levanta_external_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red", request=request)

    _con_transport(monkeypatch, handler)
    with pytest.raises(ExternalServiceError):
        await ArgentinaDatosFeriadosClient().fetch(2025)


async def test_fetch_con_payload_que_no_es_lista_levanta_external_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _con_transport(monkeypatch, lambda request: httpx.Response(200, json={"error": "x"}))

    with pytest.raises(ExternalServiceError, match="no es una lista"):
        await ArgentinaDatosFeriadosClient().fetch(2026)
