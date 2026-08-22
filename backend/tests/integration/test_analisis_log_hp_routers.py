"""Routers de analisis-log-hp por HTTP (ASGITransport sobre la app real), sin DB
ni servicios externos: identidad y catálogo de módulos fake vía
`dependency_overrides`/monkeypatch, y los factories de repos/gateways del módulo
reemplazados por los fakes en memoria de tests/unit. Cubre, por router, un camino
feliz, el 403 sin grant y el contrato de `preview_analysis` (400 validación / 200)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

import src.modules.analisis_log_hp.presentation.analysis_router as analysis_router
import src.modules.analisis_log_hp.presentation.cpmd_router as cpmd_router
import src.modules.analisis_log_hp.presentation.error_codes_router as error_codes_router
import src.modules.analisis_log_hp.presentation.saved_analyses_router as saved_router
import src.modules.analisis_log_hp.presentation.sds_router as sds_router
import src.modules.auth.presentation.dependencies.permissions as perms
from src.modules.auth.application.dtos.results import Identity, PermissionView, UserView
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.app import app
from tests.unit.application.analisis_log_hp.fake_gateways import (
    FakeAiGateway,
    FakeHpPortalGateway,
)
from tests.unit.application.analisis_log_hp.fakes import (
    FakeCpmdRepo,
    FakeErrorCodeRepo,
    FakeSavedAnalysisRepo,
    make_error_code,
)

_PREFIX = "/api/analisis-log-hp"
_MODULE = "analisis-log-hp"
_TSV = (
    "Tipo\tCódigo\tFecha\tContador\tFirmware\tAyuda\n"
    "Error\t13.20.01\t05-ago-2026 09:05:00\t100\tFW\t\n"
    "Error\t13.20.01\t05-ago-2026 10:05:00\t120\tFW\t\n"
    "Info\t99.00.01\t05-ago-2026 11:05:00\t130\tFW\t\n"
)


class _FakeCatalog:
    def __init__(self, _db: Any) -> None:
        pass

    async def is_enabled(self, module: ModuleKey) -> bool:
        return True


def _identity(*grants: tuple[str, str]) -> Identity:
    return Identity(
        user=UserView(
            id=uuid.uuid4(),
            email="op@example.com",
            full_name="Operador",
            is_superadmin=False,
            color=None,
        ),
        permissions=frozenset(PermissionView(module=m, action=a) for m, a in grants),
        session_id=uuid.uuid4(),
    )


async def _no_db() -> AsyncIterator[None]:
    yield None


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _install_session(monkeypatch: pytest.MonkeyPatch, *grants: tuple[str, str]) -> None:
    monkeypatch.setattr(perms, "SqlAlchemyModuleCatalogRepository", _FakeCatalog)
    app.dependency_overrides[get_current_identity] = lambda: _identity(*grants)
    app.dependency_overrides[get_db] = _no_db


def _uninstall_session() -> None:
    app.dependency_overrides.pop(get_current_identity, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    _install_session(monkeypatch, (_MODULE, "view"))
    yield None
    _uninstall_session()


@pytest.fixture
def _sesion_sin_grant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    _install_session(monkeypatch, ("insumos", "view"))
    yield None
    _uninstall_session()


@pytest.fixture
def error_code_repo(monkeypatch: pytest.MonkeyPatch) -> FakeErrorCodeRepo:
    repo = FakeErrorCodeRepo([make_error_code("13.20.01", description="Atasco")])
    monkeypatch.setattr(analysis_router, "get_error_code_repo", lambda _db: repo)
    monkeypatch.setattr(error_codes_router, "get_error_code_repo", lambda _db: repo)
    return repo


# --- Autenticación / autorización ------------------------------------------


async def test_sin_sesion_devuelve_401() -> None:
    async with _client() as client:
        response = await client.post(f"{_PREFIX}/analysis/preview", json={"logs": ""})

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", f"{_PREFIX}/analysis/preview"),
        ("POST", f"{_PREFIX}/analysis/validate"),
        ("GET", f"{_PREFIX}/error-codes"),
        ("POST", f"{_PREFIX}/error-codes/upsert"),
        ("GET", f"{_PREFIX}/saved-analyses"),
        ("POST", f"{_PREFIX}/sds/extract-logs"),
        ("POST", f"{_PREFIX}/sds/devices/7/refresh-cache"),
        ("GET", f"{_PREFIX}/cpmd/pdf-url?model_family=M404"),
    ],
)
async def test_sesion_valida_sin_grant_devuelve_403(method: str, path: str) -> None:
    async with _client() as client:
        response = await client.request(method, path, json={"logs": "x"})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "error_code_repo")
async def test_upsert_con_solo_view_devuelve_403() -> None:
    """Las mutaciones del catálogo exigen `manage`, no alcanza con `view`."""
    async with _client() as client:
        response = await client.post(
            f"{_PREFIX}/error-codes/upsert", json={"code": "13.20.01", "severity": "ERROR"}
        )

    assert response.status_code == 403


# --- analysis_router ---------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "error_code_repo")
async def test_preview_sin_logs_es_error_de_validacion() -> None:
    """Body inválido (falta `logs`): el handler global traduce el 422 de FastAPI
    al envelope 400 VALIDATION_ERROR del repo (test_error_handling.py)."""
    async with _client() as client:
        response = await client.post(f"{_PREFIX}/analysis/preview", json={})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.usefixtures("_sesion_view", "error_code_repo")
async def test_preview_devuelve_eventos_incidentes_y_codigos_nuevos() -> None:
    async with _client() as client:
        response = await client.post(f"{_PREFIX}/analysis/preview", json={"logs": _TSV})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "events", "incidents", "global_severity", "events_count", "codes_new", "errors"
    }
    assert body["events_count"] == 3
    assert [e["code"] for e in body["events"]] == ["13.20.01", "13.20.01", "99.00.01"]
    assert body["events"][0]["code_description"] == "Atasco"
    assert body["events"][0]["counter"] == 100
    assert body["codes_new"] == ["99.00.01"]
    assert body["errors"] == []
    assert body["global_severity"] == "ERROR"
    incidente = next(i for i in body["incidents"] if i["code"] == "13.20.01")
    assert incidente["occurrences"] == 2
    assert incidente["counter_range"] == [100, 120]
    assert incidente["code_description"] == "Atasco"


@pytest.mark.usefixtures("_sesion_view", "error_code_repo")
async def test_preview_reporta_lineas_no_parseables() -> None:
    logs = _TSV + "esto no es una fila\n"
    async with _client() as client:
        response = await client.post(f"{_PREFIX}/analysis/preview", json={"logs": logs})

    assert response.status_code == 200
    errores = response.json()["errors"]
    assert len(errores) == 1
    assert set(errores[0]) == {"line_number", "raw_line", "reason"}
    assert errores[0]["raw_line"] == "esto no es una fila"


@pytest.mark.usefixtures("_sesion_view", "error_code_repo")
async def test_validate_devuelve_codigos_fuera_del_catalogo() -> None:
    async with _client() as client:
        response = await client.post(f"{_PREFIX}/analysis/validate", json={"logs": _TSV})

    assert response.status_code == 200
    assert response.json() == {"codes_new": ["99.00.01"]}


# --- error_codes_router ------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "error_code_repo")
async def test_listar_codigos_de_error_paginado() -> None:
    async with _client() as client:
        response = await client.get(f"{_PREFIX}/error-codes", params={"page": 1, "size": 10})

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["page"], body["size"]) == (1, 1, 10)
    assert body["items"][0]["code"] == "13.20.01"
    assert body["items"][0]["description"] == "Atasco"


# --- sds_router --------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view")
async def test_refresh_cache_devuelve_baseline_del_portal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    portal = FakeHpPortalGateway()
    monkeypatch.setattr(sds_router, "get_hp_portal_gateway", lambda: portal)

    async with _client() as client:
        response = await client.post(f"{_PREFIX}/sds/devices/777/refresh-cache")

    assert response.status_code == 200
    assert response.json() == {
        "baseline": [{"operation": "RefreshHPCloudDeviceActionCache", "sent": "ayer"}]
    }
    assert portal.calls == [("refresh_hp_cache", "777")]


# --- cpmd_router -------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view")
async def test_pdf_url_resuelve_manual_por_familia(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = FakeCpmdRepo()
    manual = await repo.create(keywords=["M404"], label="LaserJet M404", filename="m404.pdf")
    monkeypatch.setattr(cpmd_router, "get_cpmd_manual_repo", lambda _db: repo)

    async with _client() as client:
        ok = await client.get(f"{_PREFIX}/cpmd/pdf-url", params={"model_family": "HP M404dn"})
        missing = await client.get(f"{_PREFIX}/cpmd/pdf-url", params={"model_family": "E877"})

    assert ok.status_code == 200
    assert ok.json() == {
        "url": f"{_PREFIX}/cpmd/{manual.id}/file", "label": "LaserJet M404"
    }
    assert missing.status_code == 404


# --- saved_analyses_router ---------------------------------------------------


@pytest.mark.usefixtures("_sesion_view")
async def test_listar_analisis_guardados(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = FakeSavedAnalysisRepo()
    snap = repo.seed(equipment_identifier="HP (SER1)")
    monkeypatch.setattr(saved_router, "get_saved_analysis_repo", lambda _db: repo)

    async with _client() as client:
        response = await client.get(f"{_PREFIX}/saved-analyses")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(snap.id)
    assert body["items"][0]["equipment_identifier"] == "HP (SER1)"
    assert body["items"][0]["global_severity"] == "ERROR"


@pytest.mark.usefixtures("_sesion_view")
async def test_ai_diagnose_devuelve_diagnostico_tokens_y_costo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = FakeAiGateway(text="Despachar técnico")
    monkeypatch.setattr(analysis_router, "get_ai_gateway", lambda: ai)

    async with _client() as client:
        response = await client.post(
            f"{_PREFIX}/analysis/ai-diagnose", json={"payload": {"serial": "S1"}}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"] == "Despachar técnico"
    assert body["tokens"] == ai.tokens
    assert body["cost_usd"] > 0
    assert ai.calls == [("diagnose", {"serial": "S1"}, "claude-sonnet-4-6")]
