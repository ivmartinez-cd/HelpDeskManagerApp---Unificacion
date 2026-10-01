"""`/api/tareas-varias` por HTTP: permisos por endpoint, técnico resuelto desde la
sesión (nunca del cliente) y supervisor que no aprueba lo propio."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass

import pytest

import src.modules.tareas_varias.presentation.tareas_varias_router as router_module
from src.modules.tareas_varias.application.use_cases.crear_solicitud_tv import CrearSolicitudTv
from src.modules.tareas_varias.application.use_cases.crear_solicitud_tv_admin import (
    CrearSolicitudTvAdmin,
)
from src.modules.tareas_varias.application.use_cases.crear_solicitud_tv_propia import (
    CrearSolicitudTvPropia,
)
from src.modules.tareas_varias.application.use_cases.decidir_solicitud_tv import (
    DecidirSolicitudTv,
)
from src.modules.tareas_varias.application.use_cases.listar_solicitudes_tv import (
    ListarSolicitudesTv,
)
from src.modules.tareas_varias.application.use_cases.listar_solicitudes_tv_propias import (
    ListarSolicitudesTvPropias,
)
from src.modules.tareas_varias.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from tests.integration.router_testing import client, install_session, uninstall_session
from tests.unit.application.tareas_varias.fakes import (
    FakeSolicitudTvRepository,
    FakeTecnicoIdentityGateway,
)

URL = "/api/tareas-varias"
_CREAR = ("tareas-varias", "create")
_APROBAR = ("tareas-varias", "approve")
_TAREA = {
    "fecha": "2026-09-15",
    "razon_social": "Exolgan",
    "sucursal": "Dock Sur",
    "tarea_realizada": "Traslado de toner",
}


@dataclass
class _Mundo:
    repo: FakeSolicitudTvRepository
    identidades: FakeTecnicoIdentityGateway


@pytest.fixture
def mundo(monkeypatch: pytest.MonkeyPatch) -> Iterator[_Mundo]:
    m = _Mundo(FakeSolicitudTvRepository(), FakeTecnicoIdentityGateway())
    builders = {
        "build_crear_solicitud_tv_propia": lambda _db: CrearSolicitudTvPropia(
            m.identidades, CrearSolicitudTv(m.repo)
        ),
        "build_crear_solicitud_tv_admin": lambda _db: CrearSolicitudTvAdmin(m.repo, m.identidades),
        "build_listar_solicitudes_tv": lambda _db: ListarSolicitudesTv(m.repo),
        "build_listar_solicitudes_tv_propias": lambda _db: ListarSolicitudesTvPropias(
            m.identidades, m.repo
        ),
        "build_decidir_solicitud_tv": lambda _db: DecidirSolicitudTv(m.repo, m.identidades),
    }
    for nombre, builder in builders.items():
        monkeypatch.setattr(router_module, nombre, builder)
    yield m
    uninstall_session()


def _vincular(m: _Mundo, user_id: uuid.UUID, id_tecnico: int) -> None:
    m.identidades._vinculos[user_id] = TecnicoVinculado(id_tecnico, f"CD - Técnico {id_tecnico}")


async def test_sin_permiso_es_403(mundo: _Mundo, monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch)
    async with client() as c:
        assert (await c.post(URL, json=_TAREA)).status_code == 403
        assert (await c.get(URL, params={"periodo": 202609})).status_code == 403


async def test_el_tecnico_carga_la_propia_y_la_ve_en_mias(
    mundo: _Mundo, monkeypatch: pytest.MonkeyPatch
) -> None:
    identidad = install_session(monkeypatch, _CREAR)
    _vincular(mundo, identidad.user.id, 1314)
    async with client() as c:
        creada = await c.post(URL, json={**_TAREA, "id_tecnico": 9999})
        mias = await c.get(f"{URL}/mias", params={"periodo": 202609})

    assert creada.status_code == 201
    assert creada.json()["id_tecnico"] == 1314  # el del vínculo, no el que mande el cliente
    assert [s["id"] for s in mias.json()["items"]] == [creada.json()["id"]]


async def test_supervisor_aprueba_ajena_pero_no_la_propia(
    mundo: _Mundo, monkeypatch: pytest.MonkeyPatch
) -> None:
    supervisor = install_session(monkeypatch, _APROBAR)
    _vincular(mundo, supervisor.user.id, 77)
    async with client() as c:
        ajena = await c.post(f"{URL}/a-nombre-de/1314", json={**_TAREA, "tecnico": "CD - Otro"})
        propia = await c.post(f"{URL}/a-nombre-de/77", json={**_TAREA, "tecnico": "CD - Yo"})
        cola = await c.get(URL, params={"periodo": 202609, "estado": "APROBADA"})

    assert ajena.status_code == 201 and ajena.json()["estado"] == "APROBADA"
    assert propia.status_code == 403
    assert propia.json()["code"] == "AUTOAPROBACION_TV"
    assert [s["id"] for s in cola.json()["items"]] == [ajena.json()["id"]]


async def test_decidir_rechaza_con_motivo(mundo: _Mundo, monkeypatch: pytest.MonkeyPatch) -> None:
    tecnico = install_session(monkeypatch, _CREAR)
    _vincular(mundo, tecnico.user.id, 1314)
    async with client() as c:
        creada = (await c.post(URL, json=_TAREA)).json()
    install_session(monkeypatch, _APROBAR)
    async with client() as c:
        r = await c.patch(
            f"{URL}/{creada['id']}/decision", json={"decision": "RECHAZADA", "motivo": "Duplicada"}
        )

    assert r.status_code == 200
    assert (r.json()["estado"], r.json()["motivo_rechazo"]) == ("RECHAZADA", "Duplicada")
