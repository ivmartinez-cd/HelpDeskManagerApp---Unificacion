"""Router de escritura de Insumos > Despachados por HTTP, sin DB ni OCA/Siges: acciones y
cierre de alerta con los casos de uso reales sobre fakes en memoria, y "Actualizar ahora"
con el lanzador, la consulta del estado y el candado reemplazados por monkeypatch (acá no
corre ninguna sincronización de verdad)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import date

import pytest

import src.modules.insumos.presentation.despachados_acciones_router as acciones_router
from src.modules.insumos.application.use_cases.despachados.acciones_despacho import (
    AccionDespachoPorts,
    CerrarAlertaDespacho,
    RegistrarAccionDespacho,
)
from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ConsultarActualizacion,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from tests.integration.router_testing import client, install_session, uninstall_session
from tests.unit.application.insumos.despachados.fakes_consulta_despachos import (
    MundoConsulta,
    corrida,
)
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    GUIA_A,
    VERDE,
    envio,
)

_BASE = "/api/insumos/despachados"
_ACCION = {"tipo": "llamado_cliente", "detalle": "Llamé al cliente", "resultado": "pendiente"}
_NARANJA = replace(VERDE, color=ColorSemaforo.NARANJA, alerta=True)


class _CandadoFake:
    def __init__(self, libre: bool) -> None:
        self.libre = libre

    @asynccontextmanager
    async def hold(self) -> AsyncIterator[bool]:
        yield self.libre


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_update(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"), ("insumos", "update"))
    yield None
    uninstall_session()


@pytest.fixture
def mundo(monkeypatch: pytest.MonkeyPatch) -> MundoConsulta:
    mundo = MundoConsulta()
    mundo.envios.envios[GUIA_A] = envio(clasificacion=_NARANJA)
    ports = AccionDespachoPorts(envios=mundo.envios, acciones=mundo.acciones, reloj=lambda: AHORA)
    monkeypatch.setattr(
        acciones_router,
        "build_registrar_accion_despacho",
        lambda _db: RegistrarAccionDespacho(ports),
    )
    monkeypatch.setattr(
        acciones_router, "build_cerrar_alerta_despacho", lambda _db: CerrarAlertaDespacho(ports)
    )
    monkeypatch.setattr(
        acciones_router,
        "build_consultar_actualizacion",
        lambda _db: ConsultarActualizacion(mundo.ports()),
    )
    return mundo


@pytest.fixture
def lanzadas(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    registro: list[str] = []
    monkeypatch.setattr(acciones_router, "lanzar_actualizacion_manual", registro.append)
    return registro


def _candado(monkeypatch: pytest.MonkeyPatch, *, libre: bool) -> None:
    monkeypatch.setattr(acciones_router, "get_despachados_lock", lambda: _CandadoFake(libre))


# --- Permisos --------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "mundo", "lanzadas")
@pytest.mark.parametrize(
    ("path", "body"),
    [
        (f"{_BASE}/actualizar", None),
        (f"{_BASE}/{GUIA_A}/acciones", _ACCION),
        (f"{_BASE}/{GUIA_A}/cerrar-alerta", None),
    ],
)
async def test_post_con_solo_view_devuelve_403(path: str, body: dict[str, str] | None) -> None:
    async with client() as c:
        response = await c.post(path, json=body)

    assert response.status_code == 403


# --- Actualizar ahora ------------------------------------------------------


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_actualizar_lanza_la_corrida_con_el_nombre_del_usuario(lanzadas: list[str]) -> None:
    async with client() as c:
        response = await c.post(f"{_BASE}/actualizar")

    assert response.status_code == 202
    assert response.json() == {"enCurso": True}
    assert lanzadas == ["Operador"]


@pytest.mark.usefixtures("_sesion_update")
async def test_actualizar_con_corrida_en_curso_devuelve_409(
    monkeypatch: pytest.MonkeyPatch, mundo: MundoConsulta, lanzadas: list[str]
) -> None:
    mundo.corridas.corridas = [corrida(1, None)]
    _candado(monkeypatch, libre=False)
    async with client() as c:
        response = await c.post(f"{_BASE}/actualizar")

    assert response.status_code == 409
    assert response.json()["code"] == "SINCRONIZACION_DESPACHOS_EN_CURSO"
    assert lanzadas == []


@pytest.mark.usefixtures("_sesion_update")
async def test_actualizar_con_corrida_colgada_y_candado_libre_lanza_igual(
    monkeypatch: pytest.MonkeyPatch, mundo: MundoConsulta, lanzadas: list[str]
) -> None:
    mundo.corridas.corridas = [corrida(1, None)]
    _candado(monkeypatch, libre=True)
    async with client() as c:
        response = await c.post(f"{_BASE}/actualizar")

    assert response.status_code == 202
    assert lanzadas == ["Operador"]


# --- Acciones --------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_update")
async def test_registrar_accion_devuelve_201_en_camel_case(mundo: MundoConsulta) -> None:
    body = {**_ACCION, "detalle": "  Llamé al cliente  ", "cerrarAlerta": True}
    async with client() as c:
        response = await c.post(f"{_BASE}/{GUIA_A}/acciones", json=body)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "guia": GUIA_A,
        "tipo": "llamado_cliente",
        "detalle": "Llamé al cliente",
        "resultado": "pendiente",
        "cerroAlerta": True,
        "usuarioNombre": "Operador",
        "creadaEn": "2026-09-24T15:00:00Z",
    }
    guia, cierre = mundo.envios.cierres[0]
    assert (guia, cierre.usuario_nombre) == (GUIA_A, "Operador")
    assert cierre.usuario_id is not None


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_detalle_vacio_devuelve_400_de_dominio() -> None:
    async with client() as c:
        response = await c.post(f"{_BASE}/{GUIA_A}/acciones", json={**_ACCION, "detalle": "  "})

    assert response.status_code == 400
    assert response.json()["code"] == "ACCION_DESPACHO_INVALIDA"


@pytest.mark.usefixtures("_sesion_update", "mundo")
@pytest.mark.parametrize("campo", ["tipo", "resultado"])
async def test_tipo_o_resultado_desconocido_devuelve_400(campo: str) -> None:
    async with client() as c:
        response = await c.post(f"{_BASE}/{GUIA_A}/acciones", json={**_ACCION, campo: "otra"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_accion_sobre_guia_no_seguida_devuelve_404() -> None:
    async with client() as c:
        response = await c.post(f"{_BASE}/9999999999999999999/acciones", json=_ACCION)

    assert response.status_code == 404


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_accion_sobre_guia_invalida_devuelve_400() -> None:
    async with client() as c:
        response = await c.post(f"{_BASE}/123/acciones", json=_ACCION)

    assert response.status_code == 400


# --- Cerrar alerta ---------------------------------------------------------


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_cerrar_alerta_sin_acciones_devuelve_409() -> None:
    async with client() as c:
        response = await c.post(f"{_BASE}/{GUIA_A}/cerrar-alerta")

    assert response.status_code == 409
    assert response.json()["code"] == "CIERRE_ALERTA_SIN_ACCION"


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_cerrar_alerta_devuelve_el_envio_con_el_cierre() -> None:
    async with client() as c:
        await c.post(f"{_BASE}/{GUIA_A}/acciones", json=_ACCION)
        response = await c.post(f"{_BASE}/{GUIA_A}/cerrar-alerta")

    assert response.status_code == 200
    envio_out = response.json()
    assert (envio_out["guia"], envio_out["color"]) == (GUIA_A, "naranja")
    assert (envio_out["alerta"], envio_out["alertaAbierta"]) == (True, False)
    assert envio_out["cierreAlerta"] == {
        "cerradaEn": "2026-09-24T15:00:00Z",
        "usuarioNombre": "Operador",
    }
    assert envio_out["fechaRemito"] == date(2026, 9, 22).isoformat()
