"""Acciones del operador sobre el tablero de Proyección por HTTP (sin DB ni
Siges: equipos de ejemplo, decisiones y auditoría con fakes; el "modo real"
calcula sobre los mismos equipos de ejemplo y relee la P/L de un Siges
falso). Mismo flujo que `PanelCandidatos` + `GrillaEstimacion` v1.7: la
decisión es del proceso, P/L y métodos se guardan como acción (no como valor
congelado), la observación escrita va solo a la auditoría y todas las
acciones operan sobre la fila efectiva (`EquipoEfectivo`)."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Any

import pytest

import src.modules.contadores.application.use_cases.proyeccion_operador.acciones as acciones_module
import src.modules.contadores.application.use_cases.proyeccion_operador.fila_vigente as vigente_module  # noqa: E501
import src.modules.contadores.presentation.proyeccion_candidatos_router as candidatos_router
from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo import entrada_ejemplo
from src.modules.contadores.application.use_cases.proyeccion_operador.auditoria import (
    RegistroAccion,
    campos_resultado,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.contexto_ejemplo import (
    contexto_ejemplo,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.dependencias import (
    DependenciasProyeccion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from tests.integration.router_testing import client, install_session, uninstall_session

_BASE = "/api/contadores/proyeccion/candidatos"
# Equipos de ejemplo: CD0004MONO (parque), CD0010MONO (sin datos: pendiente)
# y CD0007MONO (entre reales: 50.000 → 55.172).
_EQUIPO_PARQUE = 6
_EQUIPO_SIN_DATOS = 8
_EQUIPO_ENTRE_REALES = 4
_PL_VALIDA = {
    "partida": {"fecha": "2026-01-31", "valor": 40000, "tipo_toma": 1, "id_contador": 11},
    "llegada": {"fecha": "2026-03-02", "valor": 43000, "tipo_toma": 1, "id_contador": 12},
}
_PROCESO_REAL = 5501
_SELECCION_REAL = {
    "nro_proceso": _PROCESO_REAL,
    "id_grupo_economico": 1,
    "id_anexo": 1,
    "fecha_objetivo": "2026-04-30",
}
# Lo que Siges tiene para el equipo: la Llegada es un T4 con Para_Facturar=0.
_LECTURAS_SIGES = {
    11: LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, 11, True),
    12: LecturaElegidaDto(date(2026, 3, 2), 43_000, 4, 12, False),
}
_T0 = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)


class _DecisionesFake:
    def __init__(self) -> None:
        self.guardadas: list[tuple[ClaveDecisionDto, DecisionOperadorDto]] = []
        self.vigentes: dict[ClaveDecisionDto, DecisionOperadorDto] = {}

    async def obtener(self, clave: ClaveDecisionDto) -> DecisionOperadorDto | None:
        return self.vigentes.get(clave)

    async def listar_por_proceso(
        self, nro_proceso: int
    ) -> dict[tuple[int, str], DecisionOperadorDto]:
        return {}

    async def guardar(self, clave: ClaveDecisionDto, decision: DecisionOperadorDto) -> None:
        self.guardadas.append((clave, decision))


class _Entorno:
    def __init__(self) -> None:
        self.decisiones = _DecisionesFake()
        self.auditoria: list[RegistroAccion] = []
        self.nros_proceso: list[int | None] = []


@pytest.fixture
def entorno(monkeypatch: pytest.MonkeyPatch) -> Iterator[_Entorno]:
    e = _Entorno()

    class _Deps(DependenciasProyeccion):
        def decisiones(self, nro_proceso: int | None) -> Any:
            e.nros_proceso.append(nro_proceso)
            return e.decisiones

    async def _registrar(_estim_log: Any, _operador: Any, registro: RegistroAccion) -> None:
        e.auditoria.append(registro)

    async def _entrada_de(
        id_maquina: int, clase: str, _seleccion: Any, _deps: Any, _operador: str | None = None
    ) -> EstimacionInput | None:
        return entrada_ejemplo(id_maquina, clase, await contexto_ejemplo(None))

    async def _releer_siges(_id_maquina: int, _clase: str) -> dict[int, LecturaElegidaDto]:
        return dict(_LECTURAS_SIGES)

    deps = _Deps(e.decisiones, e.decisiones, lambda: None, _releer_siges, None)  # type: ignore[arg-type]
    monkeypatch.setattr(candidatos_router, "dependencias_proyeccion", lambda _db: deps)
    for module in (vigente_module, acciones_module):
        monkeypatch.setattr(module, "entrada_de", _entrada_de)
    monkeypatch.setattr(acciones_module, "registrar_accion", _registrar)
    install_session(monkeypatch, superadmin=True)
    yield e
    uninstall_session()


def _clave_real(id_maquina: int) -> ClaveDecisionDto:
    return ClaveDecisionDto(_PROCESO_REAL, id_maquina, "10")


async def test_marcar_pendiente_guarda_la_accion_y_audita_la_nota(entorno: _Entorno) -> None:
    """La observación va a la auditoría (`Estim_Log.Observacion`), no a la
    decisión de la fila."""
    body = {**_SELECCION_REAL, "nota": " sin acceso "}
    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_ENTRE_REALES}/10/marcar-pendiente", json=body)

    assert r.status_code == 204
    clave = _clave_real(_EQUIPO_ENTRE_REALES)
    assert entorno.decisiones.guardadas == [(clave, DecisionOperadorDto("MarcarPendiente"))]
    assert set(entorno.nros_proceso) == {_PROCESO_REAL}
    registro = entorno.auditoria[0]
    assert (registro.accion, registro.nro_proceso, registro.observacion) == (
        "MarcarPendiente",
        _PROCESO_REAL,
        "sin acceso",
    )


async def test_marcar_pendiente_se_audita_no_aceptado_con_propuesto_igual_al_anterior(
    entorno: _Entorno,
) -> None:
    """`HandleMarcarPendiente`: `Aceptado = 0` y `ContadorPropuesto =
    ContadorAnterior_Valor`."""
    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_ENTRE_REALES}/10/marcar-pendiente")

    assert r.status_code == 204
    registro = entorno.auditoria[0]
    assert registro.aceptado is False
    assert registro.contador_anterior == 50_000
    assert registro.contador_propuesto == 50_000
    assert registro.resultado.estim_propuesto is None
    # `ConstruirPendiente`: `FuenteEstimacion = Sin_Estimar`, `TipoToma = 14`.
    campos = campos_resultado(registro)
    assert (campos["fuente"], campos["tipo_toma_grabado"]) == ("Sin_Estimar", 14)


async def test_fila_inexistente_devuelve_404_sin_guardar(entorno: _Entorno) -> None:
    """El legacy siempre actúa sobre una fila de la grilla cargada."""
    async with client() as c:
        r = await c.post(f"{_BASE}/777/10/marcar-pendiente", json=_SELECCION_REAL)

    assert r.status_code == 404
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


async def test_equipo_real_sin_nro_proceso_no_se_puede_atribuir(entorno: _Entorno) -> None:
    async with client() as c:
        r = await c.post(f"{_BASE}/777/10/marcar-pendiente")

    assert r.status_code in (404, 422)
    assert entorno.decisiones.guardadas == []


@pytest.mark.parametrize("falta", ["id_grupo_economico", "id_anexo", "fecha_objetivo"])
async def test_proceso_real_con_seleccion_incompleta_devuelve_422(
    entorno: _Entorno, falta: str
) -> None:
    """No se calcula contra el ejemplo una acción que se guarda en un
    proceso real."""
    body = {k: v for k, v in _SELECCION_REAL.items() if k != falta}
    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_PARQUE}/10/marcar-pendiente", json=body)

    assert r.status_code == 422
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


async def test_equipo_de_ejemplo_usa_el_proceso_de_ejemplo(entorno: _Entorno) -> None:
    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_PARQUE}/10/marcar-pendiente")

    assert r.status_code == 204
    assert entorno.decisiones.guardadas[0][0] == ClaveDecisionDto(1001, _EQUIPO_PARQUE, "10")
    assert entorno.auditoria[0].nro_proceso is None


async def test_aceptar_sugerencia_audita_lo_que_la_fila_mostraba_sin_la_nota(
    entorno: _Entorno,
) -> None:
    """`HandleAceptarSugerencia`: audita el equipo efectivo (acá, el
    automático entre reales) con `Observacion = null` aunque haya nota."""
    body = {**_SELECCION_REAL, "nota": "sin acceso"}
    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_ENTRE_REALES}/10/aceptar", json=body)

    assert r.status_code == 204
    clave = _clave_real(_EQUIPO_ENTRE_REALES)
    assert entorno.decisiones.guardadas == [(clave, DecisionOperadorDto("AceptarSugerencia"))]
    registro = entorno.auditoria[0]
    assert (registro.accion, registro.observacion) == ("AceptarSugerencia", None)
    assert (registro.resultado.fuente, registro.resultado.estim_propuesto) == (
        "Historia_Propia",
        55_172,
    )
    assert (registro.contador_anterior, registro.aceptado) == (50_000, True)


async def test_aceptar_sugerencia_sin_estimado_devuelve_422(entorno: _Entorno) -> None:
    """`PanelCandidatos` solo ofrece el botón con `Estim_Propuesto.HasValue`."""
    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_SIN_DATOS}/10/aceptar")

    assert r.status_code == 422
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


async def test_aceptar_sugerencia_no_desmarca_un_pendiente(entorno: _Entorno) -> None:
    clave = _clave_real(_EQUIPO_ENTRE_REALES)
    entorno.decisiones.vigentes[clave] = DecisionOperadorDto("MarcarPendiente", actualizado_en=_T0)

    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_ENTRE_REALES}/10/aceptar", json=_SELECCION_REAL)

    assert r.status_code == 422
    assert entorno.decisiones.guardadas == []


async def test_tras_descartar_la_fila_efectiva_vuelve_al_automatico(entorno: _Entorno) -> None:
    """Tras "Descartar y empezar limpio" (`_overrides.Clear()`): la decisión
    guardada hasta el corte ya no cuenta para el panel ni para las acciones."""
    clave = _clave_real(_EQUIPO_ENTRE_REALES)
    entorno.decisiones.vigentes[clave] = DecisionOperadorDto("MarcarPendiente", actualizado_en=_T0)
    body = {**_SELECCION_REAL, "descartar_hasta": "2026-09-24T10:00:00Z"}

    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_ENTRE_REALES}/10/aceptar", json=body)

    assert r.status_code == 204
    assert entorno.auditoria[0].resultado.fuente == "Historia_Propia"


async def test_forzar_respeta_el_corte_de_descartar(entorno: _Entorno) -> None:
    """Con la fila pendiente se ofrece "Usar entre reales"; descartada la
    decisión, la fila vuelve a historia propia y el botón ya no está."""
    clave = _clave_real(_EQUIPO_ENTRE_REALES)
    entorno.decisiones.vigentes[clave] = DecisionOperadorDto("MarcarPendiente", actualizado_en=_T0)
    body = {"id_maquina": _EQUIPO_ENTRE_REALES, "clase": "10", "metodo": "entre_reales"}

    async with client() as c:
        descartada = await c.post(
            f"{_BASE}/forzar",
            json={**body, **_SELECCION_REAL, "descartar_hasta": "2026-09-24T10:00:00Z"},
        )
        vigente = await c.post(f"{_BASE}/forzar", json={**body, **_SELECCION_REAL})

    assert descartada.status_code == 422
    assert vigente.status_code == 200
    assert entorno.decisiones.guardadas == [(clave, DecisionOperadorDto("ForzarEntreReales"))]


async def test_aceptar_con_valor_manual_del_lote_no_congela_nada(entorno: _Entorno) -> None:
    """Campos de más (`contador_propuesto`/`fuente`) se ignoran: sin P/L es
    "aceptar sugerencia" (automático), como el legacy."""
    body = {"contador_propuesto": 99999, "fuente": "Historia_Propia"}

    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_ENTRE_REALES}/10/aceptar", json=body)

    assert r.status_code == 204
    assert entorno.decisiones.guardadas[0][1].accion == "AceptarSugerencia"


async def test_aceptar_pl_guarda_la_pareja_con_sus_ids_y_audita_la_observacion(
    entorno: _Entorno,
) -> None:
    async with client() as c:
        r = await c.post(
            f"{_BASE}/{_EQUIPO_PARQUE}/10/aceptar", json={**_PL_VALIDA, "nota": "L corregida"}
        )

    assert r.status_code == 204
    _, decision = entorno.decisiones.guardadas[0]
    assert decision.accion == "PL_Manual"
    assert decision.partida is not None and decision.partida.id_contador == 11
    assert decision.llegada is not None and decision.llegada.valor == 43000
    registro = entorno.auditoria[0]
    assert registro.accion == "PL_Manual"
    assert registro.observacion == "L corregida"
    assert registro.resultado.tipo_toma == 14
    assert registro.detalle["partida_id_contador"] == 11


async def test_aceptar_pl_real_usa_las_lecturas_de_siges(entorno: _Entorno) -> None:
    """La P/L es el `CandidatoContador` de Siges: lo que mande el cliente
    (valor, tipo, `Para_Facturar`) no cuenta; solo el `ID_Contador`."""
    trucada = {**_PL_VALIDA["llegada"], "valor": 99999, "tipo_toma": 1}
    body = {**_SELECCION_REAL, "partida": _PL_VALIDA["partida"], "llegada": trucada}

    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_PARQUE}/10/aceptar", json=body)

    assert r.status_code == 204
    _, decision = entorno.decisiones.guardadas[0]
    assert decision.llegada == _LECTURAS_SIGES[12]
    assert entorno.auditoria[0].resultado.t4_sin_revisar is True


@pytest.mark.parametrize(
    "llegada",
    [
        {"fecha": "2026-03-02", "valor": 43000, "tipo_toma": 1},
        {"fecha": "2026-03-02", "valor": 43000, "tipo_toma": 1, "id_contador": 99},
    ],
    ids=["sin_id_contador", "id_que_no_esta_en_siges"],
)
async def test_aceptar_pl_real_sin_lectura_de_siges_devuelve_422(
    entorno: _Entorno, llegada: dict[str, Any]
) -> None:
    body = {**_SELECCION_REAL, "partida": _PL_VALIDA["partida"], "llegada": llegada}

    async with client() as c:
        r = await c.post(f"{_BASE}/{_EQUIPO_PARQUE}/10/aceptar", json=body)

    assert r.status_code == 422
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


@pytest.mark.parametrize(
    ("partida", "llegada"),
    [
        ({"fecha": "2026-02-20", "valor": 40000, "tipo_toma": 1}, _PL_VALIDA["llegada"]),
        (_PL_VALIDA["partida"], {"fecha": "2026-03-02", "valor": 40000, "tipo_toma": 1}),
        (
            {"fecha": "2026-01-31", "valor": 40000, "tipo_toma": 14},
            _PL_VALIDA["llegada"],
        ),
    ],
    ids=["menos_de_15_dias", "llegada_igual_a_partida", "partida_estimada_t14"],
)
async def test_aceptar_pl_no_valida_devuelve_422_sin_guardar(
    entorno: _Entorno, partida: dict[str, Any], llegada: dict[str, Any]
) -> None:
    async with client() as c:
        r = await c.post(
            f"{_BASE}/{_EQUIPO_PARQUE}/10/aceptar", json={"partida": partida, "llegada": llegada}
        )

    assert r.status_code == 422
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


async def test_vista_previa_pl_no_guarda_ni_audita(entorno: _Entorno) -> None:
    body = {
        "id_maquina": _EQUIPO_PARQUE,
        "clase": "10",
        "partida_fecha": "2026-01-31",
        "partida_valor": 40000,
        "partida_tipo_toma": 1,
        "llegada_fecha": "2026-03-02",
        "llegada_valor": 43000,
        "llegada_tipo_toma": 4,
        "llegada_para_facturar": False,
    }

    async with client() as c:
        r = await c.post(f"{_BASE}/recalcular", json=body)

    assert r.status_code == 200
    # v1.7: el estimador nunca graba T4, aunque la Llegada sea un informe de ST.
    assert (r.json()["tipo_toma"], r.json()["fuente"]) == (14, "T4_ST")
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


async def test_vista_previa_real_relee_la_pl_de_siges(entorno: _Entorno) -> None:
    body = {
        **_SELECCION_REAL,
        "id_maquina": _EQUIPO_PARQUE,
        "clase": "10",
        "partida_fecha": "2026-01-31",
        "partida_valor": 1,
        "partida_tipo_toma": 1,
        "partida_id_contador": 11,
        "llegada_fecha": "2026-03-02",
        "llegada_valor": 2,
        "llegada_tipo_toma": 1,
        "llegada_id_contador": 12,
    }

    async with client() as c:
        r = await c.post(f"{_BASE}/recalcular", json=body)

    assert r.status_code == 200
    assert r.json()["fuente"] == "T4_ST"


async def test_forzar_entre_reales_se_aplica_al_toque_con_la_observacion_del_legacy(
    entorno: _Entorno,
) -> None:
    """La fila estaba marcada pendiente: "Usar entre reales" se ofrece y se
    guarda el método, no el valor."""
    clave = ClaveDecisionDto(1001, _EQUIPO_ENTRE_REALES, "10")
    entorno.decisiones.vigentes[clave] = DecisionOperadorDto("MarcarPendiente")
    body = {"id_maquina": _EQUIPO_ENTRE_REALES, "clase": "10", "metodo": "entre_reales"}

    async with client() as c:
        r = await c.post(f"{_BASE}/forzar", json=body)

    assert r.status_code == 200
    assert r.json()["estim_propuesto"] == 55_172
    assert entorno.decisiones.guardadas == [(clave, DecisionOperadorDto("ForzarEntreReales"))]
    registro = entorno.auditoria[0]
    assert registro.accion == "ForzarEntreReales"
    assert registro.observacion == "Operador forzó estimación entre reales."


@pytest.mark.parametrize(
    ("id_maquina", "metodo"),
    [
        (_EQUIPO_SIN_DATOS, "cascada_parque"),
        (_EQUIPO_SIN_DATOS, "entre_reales"),
        # `PuedeUsarCascada`: la fila ya sale de un parque.
        (_EQUIPO_PARQUE, "cascada_parque"),
        # `PuedeUsarEntreReales`: la fila ya es historia propia.
        (_EQUIPO_ENTRE_REALES, "entre_reales"),
    ],
    ids=["cascada_sin_datos", "entre_reales_sin_par", "cascada_ya_parque", "ya_entre_reales"],
)
async def test_forzar_un_metodo_que_el_legacy_no_ofrece_devuelve_422(
    entorno: _Entorno, id_maquina: int, metodo: str
) -> None:
    body = {"id_maquina": id_maquina, "clase": "10", "metodo": metodo}

    async with client() as c:
        r = await c.post(f"{_BASE}/forzar", json=body)

    assert r.status_code == 422
    assert entorno.decisiones.guardadas == []
    assert entorno.auditoria == []


async def test_no_hay_accion_de_nota_suelta(entorno: _Entorno) -> None:
    """El "+ Agregar nota" del legacy solo abre el campo de texto."""
    async with client() as c:
        r = await c.post(f"{_BASE}/777/10/nota", json={"nota": "llamar", **_SELECCION_REAL})

    assert r.status_code in (404, 405)
    assert entorno.decisiones.guardadas == []
