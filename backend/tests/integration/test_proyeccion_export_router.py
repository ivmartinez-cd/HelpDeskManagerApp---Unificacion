"""Superficie HTTP de la Proyección que agrega la paridad con el Estimador v1.7:
export a SiGes (permiso, nombre, Todos / Solo estimados, cp1252), banner de
restauración del tablero (también en el modo ejemplo), campos nuevos de la
fila, del panel de candidatos y de la vista previa. Sin DB ni Siges."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

import pytest

import src.modules.contadores.presentation._proyeccion_fila_vigente as vigente_module
import src.modules.contadores.presentation.proyeccion_router as router_module
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
)
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases.generar_export_csv import OpcionesExportCsv
from src.modules.contadores.domain.well_known_features import PROYECCION_OPERAR
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    NRO_PROCESO_EJEMPLO,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    DecisionesOperadorStore,
)
from src.shared.presentation.app import app
from tests.integration.router_testing import client, install_session, uninstall_session

_BASE = "/api/contadores/proyeccion"
_EXPORT = (
    f"{_BASE}/export?nro_proceso=5501&id_grupo_economico=9&id_anexo=3&fecha_objetivo=2026-04-30"
)
_EQUIPO_PARQUE = 6
_EQUIPO_ENTRE_REALES = 4


class _ExportFake:
    def __init__(self) -> None:
        self.llamadas: list[tuple[SolicitudTableroSigesDto, OpcionesExportCsv | None]] = []

    async def execute(
        self, solicitud: SolicitudTableroSigesDto, opciones: OpcionesExportCsv | None = None
    ) -> str:
        self.llamadas.append((solicitud, opciones))
        return "SERIE;OBSERVACION\r\nNación·ł😀;x\r\n"


@pytest.fixture
def export(monkeypatch: pytest.MonkeyPatch) -> Iterator[_ExportFake]:
    fake = _ExportFake()
    monkeypatch.setattr(router_module, "_export", lambda _db: fake)
    yield fake
    uninstall_session()


@pytest.fixture
def decisiones(monkeypatch: pytest.MonkeyPatch) -> Iterator[DecisionesOperadorStore]:
    store = DecisionesOperadorStore()
    monkeypatch.setattr(router_module, "get_decisiones_operador_store", lambda: store)
    monkeypatch.setattr(vigente_module, "decisiones_de", lambda _nro, _db: store)
    install_session(monkeypatch, superadmin=True)
    yield store
    uninstall_session()


# ── Export ─────────────────────────────────────────────────────────────────────


async def test_export_cp1252_con_best_fit_y_nombre_del_legacy(
    export: _ExportFake, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, superadmin=True)
    async with client() as c:
        r = await c.get(_EXPORT)

    assert r.status_code == 200
    assert r.content == "SERIE;OBSERVACION\r\nNación·l??;x\r\n".encode("cp1252")
    assert r.headers["content-type"] == "text/csv; charset=windows-1252"
    assert r.headers["content-disposition"] == 'attachment; filename="Estimacion_5501_20260430.csv"'
    solicitud, opciones = export.llamadas[0]
    # `operador` = el usuario autenticado: exporta la grilla que cargó él.
    assert solicitud == SolicitudTableroSigesDto(
        5501, 9, 3, date(2026, 4, 30), solicitud.operador
    )
    assert solicitud.operador is not None
    assert opciones == OpcionesExportCsv(False, None)


async def test_export_solo_estimados_y_descartar_hasta(
    export: _ExportFake, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, superadmin=True)
    async with client() as c:
        r = await c.get(f"{_EXPORT}&solo_estimados=true&descartar_hasta=2026-05-02T10:00:00Z")

    assert r.headers["content-disposition"].endswith('_20260430_estimados.csv"')
    assert export.llamadas[0][1] == OpcionesExportCsv(True, datetime(2026, 5, 2, 10, 0, tzinfo=UTC))


async def test_export_alcanza_con_el_permiso_que_opera_la_grilla(
    export: _ExportFake, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity = install_session(monkeypatch)
    operador = replace(identity, features=frozenset({PROYECCION_OPERAR.value}))
    app.dependency_overrides[get_current_identity] = lambda: operador
    async with client() as c:
        r = await c.get(_EXPORT)

    assert r.status_code == 200


async def test_export_con_permiso_manage(
    export: _ExportFake, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, ("contadores", "manage"))
    async with client() as c:
        r = await c.get(_EXPORT)

    assert r.status_code == 200


async def test_export_sin_permiso_para_operar_es_403(
    export: _ExportFake, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, ("contadores", "view"))
    async with client() as c:
        r = await c.get(_EXPORT)

    assert r.status_code == 403
    assert export.llamadas == []


# ── Tablero ────────────────────────────────────────────────────────────────────


async def test_tablero_ejemplo_restaura_las_decisiones_y_expone_el_banner(
    decisiones: DecisionesOperadorStore,
) -> None:
    clave = ClaveDecisionDto(NRO_PROCESO_EJEMPLO, _EQUIPO_PARQUE, "10")
    await decisiones.guardar(clave, DecisionOperadorDto("MarcarPendiente"))

    async with client() as c:
        r = await c.get(f"{_BASE}/tablero")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["restauracion"]["restauradas"] == 1
    assert cuerpo["restauracion"]["vigentes_hasta"] is not None
    fila = next(f for f in cuerpo["filas"] if f["id_maquina"] == _EQUIPO_PARQUE)
    assert (fila["fuente"], fila["estim_propuesto"], fila["editado_por_operador"]) == (
        "Pendiente",
        None,
        True,
    )
    campos_nuevos = {
        "detalle_calculo",
        "fecha_toma_actual",
        "guia_operador",
        "metodo",
        "etiqueta_nivel",
        "t4_sin_revisar",
        "meses_sin_real_en_alerta",
    }
    assert campos_nuevos <= fila.keys()


async def test_tablero_descartar_hasta_ignora_lo_decidido_antes(
    decisiones: DecisionesOperadorStore,
) -> None:
    clave = ClaveDecisionDto(NRO_PROCESO_EJEMPLO, _EQUIPO_PARQUE, "10")
    await decisiones.guardar(clave, DecisionOperadorDto("MarcarPendiente"))
    hasta = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    async with client() as c:
        r = await c.get(f"{_BASE}/tablero", params={"descartar_hasta": hasta})

    cuerpo = r.json()
    assert cuerpo["restauracion"]["restauradas"] == 0
    fila = next(f for f in cuerpo["filas"] if f["id_maquina"] == _EQUIPO_PARQUE)
    assert fila["fuente"] != "Pendiente"


# ── Panel de candidatos ────────────────────────────────────────────────────────


async def test_candidatos_exponen_lecturas_completas_y_metodos_disponibles(
    decisiones: DecisionesOperadorStore,
) -> None:
    async with client() as c:
        r = await c.get(f"{_BASE}/candidatos/{_EQUIPO_ENTRE_REALES}/10")

    assert r.status_code == 200
    cuerpo = r.json()
    # Ya sale de historia propia: el legacy no ofrece "Usar entre reales".
    assert cuerpo["puede_usar_entre_reales"] is False
    assert isinstance(cuerpo["puede_usar_cascada"], bool)
    lectura: dict[str, Any] = cuerpo["lecturas"][0]
    assert {"id_contador", "para_facturar", "usable", "etiqueta_validacion"} <= lectura.keys()


async def test_candidatos_ofrecen_metodos_sobre_la_fila_efectiva_tras_descartar(
    decisiones: DecisionesOperadorStore,
) -> None:
    """`OnOjoClick` usa `EquipoEfectivo`: con la fila marcada pendiente se
    ofrece "Usar entre reales"; tras "Descartar y empezar limpio" la fila
    vuelve a historia propia y el botón desaparece."""
    clave = ClaveDecisionDto(NRO_PROCESO_EJEMPLO, _EQUIPO_ENTRE_REALES, "10")
    await decisiones.guardar(clave, DecisionOperadorDto("MarcarPendiente"))
    hasta = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    url = f"{_BASE}/candidatos/{_EQUIPO_ENTRE_REALES}/10"

    async with client() as c:
        con_decision = await c.get(url)
        descartada = await c.get(url, params={"descartar_hasta": hasta})

    assert con_decision.json()["puede_usar_entre_reales"] is True
    assert descartada.json()["puede_usar_entre_reales"] is False


async def test_candidatos_de_un_equipo_de_parque_no_ofrecen_cascada(
    decisiones: DecisionesOperadorStore,
) -> None:
    async with client() as c:
        r = await c.get(f"{_BASE}/candidatos/{_EQUIPO_PARQUE}/10")

    assert r.json()["puede_usar_cascada"] is False


async def test_vista_previa_expone_detalle_metodo_y_marcas(
    decisiones: DecisionesOperadorStore,
) -> None:
    body = {
        "id_maquina": _EQUIPO_PARQUE,
        "clase": "10",
        "partida_fecha": "2026-01-31",
        "partida_valor": 40000,
        "partida_tipo_toma": 1,
        "llegada_fecha": "2026-03-02",
        "llegada_valor": 43000,
        "llegada_tipo_toma": 1,
    }
    async with client() as c:
        r = await c.post(f"{_BASE}/candidatos/recalcular", json=body)

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["metodo"] == "EntreReales"
    assert "PLManual" in cuerpo["marcas"]
    assert cuerpo["detalle_calculo"]
    assert cuerpo["etiqueta_nivel"]
    assert "guia_operador" in cuerpo
