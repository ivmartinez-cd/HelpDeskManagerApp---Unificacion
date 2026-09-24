"""Recesos de la Proyección (`Recesos.razor` v1.7) en el modo ejemplo (store
en memoria): agregar sin descripción, editar, rango invertido y 404. Sin DB
ni Siges."""

from collections.abc import Iterator

import pytest

import src.modules.contadores.presentation.proyeccion_recesos_router as recesos_module
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore
from tests.integration.router_testing import client, install_session, uninstall_session

_RECESOS = "/api/contadores/proyeccion/recesos"
_ALTA = {"id_grupo_economico": 1, "id_anexo": None, "fecha_desde": "2026-04-10",
         "fecha_hasta": "2026-04-12"}


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> Iterator[RecesosEjemploStore]:
    propio = RecesosEjemploStore()
    monkeypatch.setattr(recesos_module, "get_recesos_ejemplo_store", lambda: propio)
    monkeypatch.setattr(recesos_module, "ID_GRUPO_ECONOMICO_EJEMPLO", 1)
    install_session(monkeypatch, superadmin=True)
    yield propio
    uninstall_session()


async def test_alta_sin_descripcion_y_edicion(store: RecesosEjemploStore) -> None:
    async with client() as c:
        creado = await c.post(_RECESOS, json=_ALTA)
        id_receso = creado.json()["id"]
        editado = await c.put(
            f"{_RECESOS}/{id_receso}",
            json={**_ALTA, "id_anexo": 44, "fecha_hasta": "2026-04-20", "descripcion": "Verano"},
        )
        lista = await c.get(_RECESOS, params={"id_grupo_economico": 1})

    assert creado.status_code == 201
    assert creado.json()["descripcion"] == ""
    assert editado.status_code == 200
    assert (editado.json()["id_anexo"], editado.json()["fecha_hasta"]) == (44, "2026-04-20")
    assert [r["descripcion"] for r in lista.json()["items"]] == ["Verano"]


async def test_editar_con_rango_invertido_o_inexistente(store: RecesosEjemploStore) -> None:
    async with client() as c:
        id_receso = (await c.post(_RECESOS, json=_ALTA)).json()["id"]
        invertido = await c.put(
            f"{_RECESOS}/{id_receso}", json={**_ALTA, "fecha_desde": "2026-04-30"}
        )
        inexistente = await c.put(f"{_RECESOS}/999", json=_ALTA)

    assert invertido.status_code == 400  # ValidationError de dominio (RECESO_RANGO_INVALIDO)
    assert invertido.json()["code"] == "RECESO_RANGO_INVALIDO"
    assert inexistente.status_code == 404
