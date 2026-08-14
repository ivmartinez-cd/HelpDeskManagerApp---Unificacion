"""HttpxErsClientProvider con transporte mockeado: listado de grupos,
export a CSV y ciclo de vida del token cacheado."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

import src.modules.contadores.infrastructure.ers.httpx_ers_client_provider as provider_module
from src.modules.contadores.infrastructure.ers.httpx_ers_client_provider import (
    HttpxErsClientProvider,
)
from src.shared.domain.errors import ExternalServiceError
from tests.unit.infrastructure.contadores.settings_stub import make_settings


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("timeout", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


def _provider(tmp_path: Path, *, token: str = "Bearer viejo") -> HttpxErsClientProvider:
    token_file = tmp_path / "token.json"
    token_file.write_text(
        json.dumps({"token": token, "cookies": [{"name": "c", "value": "v"}]}),
        encoding="utf-8",
    )
    return HttpxErsClientProvider(
        settings=make_settings(epson_ers_token_file=str(token_file))
    )


async def test_list_active_customers_ordena_y_prefija(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/prod/device_groups/"
        assert request.headers["authorization"] == "Bearer viejo"
        return httpx.Response(
            200,
            json={"items": [{"id": 2, "name": "zeta"}, {"id": 1, "name": "alfa"}, {"name": "x"}]},
        )

    _patch_transport(monkeypatch, handler)

    clients = await _provider(tmp_path).list_active_customers()

    assert [c.name for c in clients] == ["EPSON - ALFA", "EPSON - ZETA"]
    assert [c.id for c in clients] == ["1", "2"]  # el item sin id se descarta


async def test_list_active_customers_renueva_el_token_ante_401(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async def fake_refresh(*, token_file_path: str, settings: Any) -> dict[str, Any]:
        return {"token": "Bearer nuevo", "cookies": []}

    monkeypatch.setattr(provider_module, "refresh_ers_token", fake_refresh)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["authorization"] == "Bearer viejo":
            return httpx.Response(401, json={})
        return httpx.Response(200, json={"items": [{"id": 1, "name": "alfa"}]})

    _patch_transport(monkeypatch, handler)

    clients = await _provider(tmp_path).list_active_customers()

    assert [c.id for c in clients] == ["1"]


async def test_list_active_customers_error_no_auth_se_reporta(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(500, text="boom"))
    with pytest.raises(ExternalServiceError, match="500"):
        await _provider(tmp_path).list_active_customers()


async def test_list_active_customers_error_de_conexion_se_envuelve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def explota(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red")

    _patch_transport(monkeypatch, explota)
    with pytest.raises(ExternalServiceError, match="conectar"):
        await _provider(tmp_path).list_active_customers()


async def test_token_cacheado_ilegible_dispara_refresh(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("{json roto", encoding="utf-8")
    refreshed: list[str] = []

    async def fake_refresh(*, token_file_path: str, settings: Any) -> dict[str, Any]:
        refreshed.append(token_file_path)
        return {"token": "Bearer nuevo", "cookies": []}

    monkeypatch.setattr(provider_module, "refresh_ers_token", fake_refresh)
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={"items": []}))

    provider = HttpxErsClientProvider(settings=make_settings(epson_ers_token_file=str(token_file)))
    assert await provider.list_active_customers() == []
    assert refreshed == [str(token_file)]


def _export_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/prod/device_groups/g1/devices/":
        return httpx.Response(200, json={"devices": ["d1"]})
    if path == "/prod/devices/d1/statuses/":
        return httpx.Response(
            200,
            json={"items": [{"upload_id": "u1", "collected_datetime": "2026-08-01T10:00:00Z"}]},
        )
    if path == "/prod/devices/d1/statuses/u1/":
        return httpx.Response(
            200,
            json={
                "serial_number": "S1",
                "device_info_json": {
                    "UsageInfo": {"PrtMarker": {"LC": 100}, "Marker": [{"TCP": 0}]}
                },
            },
        )
    return httpx.Response(500, text=f"ruta inesperada {path}")


async def test_export_meters_to_csv_escribe_el_archivo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, _export_handler)

    ruta = await _provider(tmp_path).export_meters_to_csv(
        group_id="g1",
        group_name="Cliente Uno",
        max_date="2026-08-14",
        output_dir=str(tmp_path / "salida"),
    )

    contenido = Path(ruta).read_text(encoding="utf-8")
    assert Path(ruta).name == "EPSON_Cliente_Uno_20260814_AutoCSV.csv"
    assert "S1;01/08/2026;17;10;100" in contenido


async def test_export_meters_sin_dispositivos_en_el_grupo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_transport(monkeypatch, lambda request: httpx.Response(200, json={"devices": []}))
    with pytest.raises(ExternalServiceError, match="No se encontraron dispositivos"):
        await _provider(tmp_path).export_meters_to_csv(
            group_id="g1", group_name="X", max_date="2026-08-14", output_dir=str(tmp_path)
        )


async def test_export_meters_sin_contadores_en_rango(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/prod/device_groups/g1/devices/":
            return httpx.Response(200, json={"devices": ["d1"]})
        return httpx.Response(200, json={"items": []})  # sin statuses => sin filas

    _patch_transport(monkeypatch, handler)
    with pytest.raises(ExternalServiceError, match="No se encontraron contadores"):
        await _provider(tmp_path).export_meters_to_csv(
            group_id="g1", group_name="X", max_date="2026-08-14", output_dir=str(tmp_path)
        )
