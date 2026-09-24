"""Router de lectura de Insumos > Despachados por HTTP, sin DB ni OCA/Siges: los casos de
uso reales sobre los fakes en memoria de los tests unit (`MundoConsulta`), inyectados por
monkeypatch de los builders importados en el router. Cubre 401/403, el envelope `Page[T]`,
cómo llegan los filtros al caso de uso, los 400 de validación, el 404 y los nombres de los
campos en el wire (camelCase)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest

import src.modules.insumos.presentation.despachados_router as despachados_router
from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ConsultarActualizacion,
    ListarDespachos,
    ObtenerDetalleDespacho,
    ResumirDespachos,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    ColumnaOrden,
    OrdenDespachos,
)
from tests.integration.router_testing import client, install_session, uninstall_session
from tests.unit.application.insumos.despachados.fakes_consulta_despachos import (
    CONFIG,
    MundoConsulta,
    corrida,
    fila,
)
from tests.unit.application.insumos.despachados.fakes_despachados import (
    GUIA_A,
    VERDE,
    despacho,
    envio,
    estado_oca,
)

_BASE = "/api/insumos/despachados"
_GUIA_INEXISTENTE = "9999999999999999999"


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_sin_grant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("wati", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def mundo(monkeypatch: pytest.MonkeyPatch) -> MundoConsulta:
    mundo = MundoConsulta()
    constructores = {
        "build_listar_despachos": ListarDespachos,
        "build_resumir_despachos": ResumirDespachos,
        "build_obtener_detalle_despacho": ObtenerDetalleDespacho,
    }
    for nombre, caso in constructores.items():
        monkeypatch.setattr(
            despachados_router, nombre, lambda _db, c=caso: c(mundo.ports(), CONFIG)
        )
    monkeypatch.setattr(
        despachados_router,
        "build_consultar_actualizacion",
        lambda _db: ConsultarActualizacion(mundo.ports()),
    )
    return mundo


# --- Autenticación / autorización ------------------------------------------


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(_BASE)

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
@pytest.mark.parametrize(
    "path",
    [_BASE, f"{_BASE}/requieren-accion", f"{_BASE}/resumen", f"{_BASE}/actualizacion"]
    + [f"{_BASE}/{GUIA_A}"],
)
async def test_sin_insumos_view_devuelve_403(path: str) -> None:
    async with client() as c:
        response = await c.get(path)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


# --- Listado ---------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view")
async def test_listado_pasa_filtros_y_pagina_y_devuelve_el_envelope(mundo: MundoConsulta) -> None:
    mundo.consulta.filas = [fila(GUIA_A)]
    mundo.consulta.total = 41
    params = {
        "texto": " 3867 ",
        "colores": "rojo, naranja",
        "operativa": "434324",
        "remitoDesde": "2026-09-01",
        "remitoHasta": "2026-09-20",
        "page": "3",
        "size": "10",
    }
    async with client() as c:
        response = await c.get(_BASE, params=params)

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["page"], body["size"]) == (41, 3, 10)
    assert [item["guia"] for item in body["items"]] == [GUIA_A]
    filtros, pagina = mundo.consulta.listados[0]
    assert (pagina.limite, pagina.desplazamiento) == (10, 20)
    assert filtros.texto == "3867"
    assert filtros.colores == (ColorSemaforo.ROJO, ColorSemaforo.NARANJA)
    assert filtros.operativa == "434324"
    assert (filtros.remito_desde, filtros.remito_hasta) == (date(2026, 9, 1), date(2026, 9, 20))
    assert filtros.solo_alertas_abiertas is False


@pytest.mark.usefixtures("_sesion_view")
async def test_listado_sin_filtros_usa_los_defaults(mundo: MundoConsulta) -> None:
    async with client() as c:
        response = await c.get(_BASE)

    assert response.status_code == 200
    assert (response.json()["page"], response.json()["size"]) == (1, 25)
    filtros, _ = mundo.consulta.listados[0]
    assert (filtros.texto, filtros.colores, filtros.operativa) == ("", (), None)
    assert filtros.orden == OrdenDespachos(ColumnaOrden.URGENCIA, descendente=False)


@pytest.mark.usefixtures("_sesion_view")
@pytest.mark.parametrize(("direccion", "descendente"), [("asc", False), ("desc", True)])
async def test_listado_pasa_el_orden_al_caso_de_uso(
    mundo: MundoConsulta, direccion: str, descendente: bool
) -> None:
    params = {"orden": "fecha_estado", "direccion": direccion}
    async with client() as c:
        response = await c.get(_BASE, params=params)

    assert response.status_code == 200
    filtros, _ = mundo.consulta.listados[0]
    assert filtros.orden == OrdenDespachos(ColumnaOrden.FECHA_ESTADO, descendente)


@pytest.mark.usefixtures("_sesion_view", "mundo")
async def test_color_invalido_devuelve_400_con_los_validos() -> None:
    async with client() as c:
        response = await c.get(_BASE, params={"colores": "rojo,violeta"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "violeta" in response.json()["message"]


@pytest.mark.usefixtures("_sesion_view", "mundo")
@pytest.mark.parametrize(
    "params",
    [{"size": "101"}, {"page": "0"}, {"remitoDesde": "ayer"}]
    + [{"orden": "operativa"}, {"orden": "cliente", "direccion": "arriba"}],
)
async def test_paginacion_fecha_u_orden_invalidos_devuelven_400(params: dict[str, str]) -> None:
    async with client() as c:
        response = await c.get(_BASE, params=params)

    assert response.status_code == 400


@pytest.mark.usefixtures("_sesion_view")
async def test_fila_sale_en_camel_case_con_dias_al_limite(mundo: MundoConsulta) -> None:
    rojo = fila(GUIA_A, ColorSemaforo.ROJO, alerta_abierta=True, fecha_limite=date(2026, 9, 25))
    mundo.consulta.filas = [rojo]
    async with client() as c:
        item = (await c.get(_BASE)).json()["items"][0]

    assert set(item) == {
        "guia", "color", "alertaAbierta", "observacion", "fechaLimite",
        "diasHabilesParaLimite", "estado", "motivo", "sucursalOca", "fechaEstado",
        "operativa", "cliente", "fechaRemito", "numeroRemito", "cantidadRemitos",
        "incidente", "cantidadIncidentes", "ultimaAccion", "conError",
    }  # fmt: skip
    assert item["color"] == "rojo"
    assert (item["fechaLimite"], item["diasHabilesParaLimite"]) == ("2026-09-25", 1)
    assert item["ultimaAccion"] is None


@pytest.mark.usefixtures("_sesion_view")
async def test_requieren_accion_filtra_alertas_abiertas(mundo: MundoConsulta) -> None:
    async with client() as c:
        response = await c.get(f"{_BASE}/requieren-accion")

    assert response.status_code == 200
    assert response.json()["size"] == 500
    filtros, pagina = mundo.consulta.listados[0]
    assert filtros.solo_alertas_abiertas is True
    assert pagina.limite == 500


# --- Resumen y actualización -----------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "mundo")
async def test_resumen_mapea_tarjetas() -> None:
    async with client() as c:
        response = await c.get(f"{_BASE}/resumen")

    assert response.status_code == 200
    assert response.json() == {
        "porColor": dict.fromkeys([c.value for c in ColorSemaforo], 1),
        "alertasRojas": 1,
        "alertasNaranjas": 1,
        "naranjasSinAccion": 0,
        "limiteMasProximo": "2026-09-25",
        "diasHabilesLimiteMasProximo": 1,
        "operativas": ["434324"],
    }


@pytest.mark.usefixtures("_sesion_view")
async def test_actualizacion_en_curso_con_la_ultima_terminada(mundo: MundoConsulta) -> None:
    terminada = corrida(1, datetime(2026, 9, 24, 13, 30, tzinfo=UTC))
    mundo.corridas.corridas = [terminada, corrida(2, None)]
    async with client() as c:
        response = await c.get(f"{_BASE}/actualizacion")

    assert response.status_code == 200
    assert response.json() == {
        "enCurso": True,
        "iniciadaEn": "2026-09-24T13:02:00Z",
        "ultimaTerminada": {
            "id": 1,
            "origen": "programada",
            "usuarioNombre": None,
            "iniciadaEn": "2026-09-24T13:01:00Z",
            "terminadaEn": "2026-09-24T13:30:00Z",
            "enviosNuevos": 0,
            "consultasOk": 1,
            "consultasError": 0,
            "error": None,
        },
    }


# --- Detalle ---------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "mundo")
@pytest.mark.parametrize("guia", ["123", "38675000000000000011", "386750000000000000a"])
async def test_guia_invalida_devuelve_400(guia: str) -> None:
    async with client() as c:
        response = await c.get(f"{_BASE}/{guia}")

    assert response.status_code == 400


@pytest.mark.usefixtures("_sesion_view", "mundo")
async def test_guia_no_seguida_devuelve_404() -> None:
    async with client() as c:
        response = await c.get(f"{_BASE}/{_GUIA_INEXISTENTE}")

    assert response.status_code == 404
    assert response.json()["code"] == "ENVIO_DESPACHO_NO_ENCONTRADO"


@pytest.mark.usefixtures("_sesion_view")
async def test_detalle_mapea_envio_remitos_y_estado_oca(mundo: MundoConsulta) -> None:
    rojo = replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25))
    mundo.envios.envios[GUIA_A] = envio(clasificacion=rojo, estado_oca=estado_oca(id_estado=45))
    await mundo.remitos.guardar([despacho()])
    async with client() as c:
        response = await c.get(f"{_BASE}/{GUIA_A}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"envio", "diasHabilesParaLimite", "remitos", "cambios", "acciones"}
    assert body["diasHabilesParaLimite"] == 1
    assert body["envio"]["alertaAbierta"] is True
    assert body["envio"]["estadoOca"]["idEstado"] == 45
    assert body["envio"]["cierreAlerta"] is None
    remito = body["remitos"][0]
    assert (remito["numeroRemito"], remito["entregaA"]) == (50001, "Recepción")
    assert remito["incidentes"] == [{"numero": "440001", "numeroCliente": ""}]
    assert (body["cambios"], body["acciones"]) == ([], [])
