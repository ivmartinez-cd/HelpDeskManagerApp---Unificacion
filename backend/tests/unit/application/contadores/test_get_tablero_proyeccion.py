from datetime import UTC, date, datetime

import pytest

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
    LecturaElegidaDto,
    SolicitudRestauracionDto,
)
from src.modules.contadores.application.dtos.fila_proyeccion_dto import FilaProyeccionDto
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    GetTableroProyeccionUseCase,
    ReleerLecturas,
    TableroProyeccionResult,
)

_PROCESO = 1001
_CTX = ContextoProcesoDto(
    fecha_objetivo=date(2026, 4, 30),
    periodo_desde=date(2026, 4, 1),
    periodo_hasta=date(2026, 5, 1),
    id_grupo_economico=1,
    id_anexo=1,
    recesos=[],
)
_T0 = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)


class _DecisionesFake:
    """Solo lectura: lo que el tablero consulta del puerto."""

    def __init__(self, por_proceso: dict[int, dict[tuple[int, str], DecisionOperadorDto]]) -> None:
        self._por_proceso = por_proceso
        self.consultas: list[int] = []

    async def listar_por_proceso(
        self, nro_proceso: int
    ) -> dict[tuple[int, str], DecisionOperadorDto]:
        self.consultas.append(nro_proceso)
        return dict(self._por_proceso.get(nro_proceso, {}))

    async def obtener(self, clave: ClaveDecisionDto) -> DecisionOperadorDto | None:
        raise NotImplementedError

    async def guardar(self, clave: ClaveDecisionDto, decision: DecisionOperadorDto) -> None:
        raise NotImplementedError


async def _tablero(
    decisiones: dict[tuple[int, str], DecisionOperadorDto] | None = None,
    descartar_hasta: datetime | None = None,
    releer: ReleerLecturas | None = None,
) -> TableroProyeccionResult:
    use_case = GetTableroProyeccionUseCase(
        _DecisionesFake({_PROCESO: decisiones or {}}), releer_lecturas=releer
    )
    return await use_case.execute(_CTX, SolicitudRestauracionDto(_PROCESO, descartar_hasta))


def _fila(
    resultado: TableroProyeccionResult, nro_serie: str, clase: str = "10"
) -> FilaProyeccionDto:
    return next(f for f in resultado.filas if f.nro_serie == nro_serie and f.clase == clase)


async def test_arma_una_fila_por_equipo_y_clase() -> None:
    resultado = await _tablero()

    assert len(resultado.filas) == 11  # 10 equipos, uno con 2 clases (Mono+Color)
    # "Total equipos" cuenta máquinas físicas distintas (parque), no filas.
    assert resultado.resumen.total == 10


async def test_equipo_real_muestra_el_contador_actual_y_las_impresiones_reales() -> None:
    fila = _fila(await _tablero(), "CD0001MONO")

    assert fila.es_real is True
    assert fila.semaforo == "VERDE"
    assert fila.estim_propuesto == 122_300
    assert fila.impresiones == 3_800  # FC_ImpresionesReales, no valor − anterior
    assert fila.tipo_toma == 1  # tipo del contador actual, no del anterior
    assert fila.fecha_toma_actual == date(2026, 4, 28)


async def test_equipo_salto_imposible_es_rojo_con_borde() -> None:
    fila = _fila(await _tablero(), "CD0005MONO")

    assert fila.semaforo == "ROJO"
    assert fila.borde_salto_imposible is True


async def test_equipo_mono_color_genera_dos_filas() -> None:
    resultado = await _tablero()

    filas = [f for f in resultado.filas if f.nro_serie == "CD0011COLOR"]
    assert {f.clase for f in filas} == {"10", "20"}


async def test_kpi_estimados_son_las_filas_a_estimar_sin_pendientes() -> None:
    """`GrillaEstimacion.CantEstimados` del legacy: 11 filas, 1 real y 1
    pendiente → 9 estimadas (antes HDM contaba total − reales = 10)."""
    resumen = (await _tablero()).resumen

    assert (resumen.reales, resumen.pendientes, resumen.estimados) == (1, 1, 9)
    assert resumen.sospechosos == 1


async def test_historico_termina_con_el_periodo_actual() -> None:
    fila = _fila(await _tablero(), "CD0001MONO")

    assert len(fila.historico_12) == 12
    assert fila.historico_12[-1] == 3_800


async def test_sin_solicitud_de_restauracion_no_consulta_decisiones() -> None:
    fake = _DecisionesFake({_PROCESO: {(4, "10"): DecisionOperadorDto("MarcarPendiente")}})

    resultado = await GetTableroProyeccionUseCase(fake).execute(_CTX)

    assert fake.consultas == []
    assert _fila(resultado, "CD0007MONO").fuente == "Historia_Propia"


async def test_restaura_la_decision_del_proceso_y_la_cuenta() -> None:
    decisiones = {(4, "10"): DecisionOperadorDto("MarcarPendiente")}

    resultado = await _tablero(decisiones)

    fila = _fila(resultado, "CD0007MONO")
    assert fila.estim_propuesto is None
    assert fila.fuente == "Pendiente"
    assert fila.editado_por_operador is True
    assert resultado.resumen.pendientes == 2
    assert resultado.resumen.estimados == 8
    assert (resultado.restauracion.restauradas, resultado.restauracion.descartadas) == (1, 0)


async def test_decisiones_de_otro_proceso_no_se_arrastran() -> None:
    fake = _DecisionesFake({999: {(4, "10"): DecisionOperadorDto("MarcarPendiente")}})

    resultado = await GetTableroProyeccionUseCase(fake).execute(
        _CTX, SolicitudRestauracionDto(_PROCESO)
    )

    assert _fila(resultado, "CD0007MONO").fuente == "Historia_Propia"
    assert resultado.restauracion.restauradas == 0


async def test_decision_sobre_una_fila_que_ya_es_real_se_descarta() -> None:
    resultado = await _tablero({(1, "10"): DecisionOperadorDto("MarcarPendiente")})

    assert _fila(resultado, "CD0001MONO").estim_propuesto == 122_300
    assert (resultado.restauracion.restauradas, resultado.restauracion.descartadas) == (0, 1)


async def test_descartar_ignora_lo_restaurado_pero_no_lo_decidido_despues() -> None:
    decisiones = {
        (4, "10"): DecisionOperadorDto("MarcarPendiente", actualizado_en=_T0),
        (5, "10"): DecisionOperadorDto(
            "MarcarPendiente", actualizado_en=datetime(2026, 9, 24, 11, 0, tzinfo=UTC)
        ),
    }

    resultado = await _tablero(decisiones, descartar_hasta=_T0)

    assert _fila(resultado, "CD0007MONO").fuente == "Historia_Propia"
    assert _fila(resultado, "CD0006MONO").fuente == "Pendiente"
    assert resultado.restauracion.vigentes_hasta == datetime(2026, 9, 24, 11, 0, tzinfo=UTC)


_Releidas = dict[tuple[int, str], dict[int, LecturaElegidaDto]]


def _pl_con_ids() -> DecisionOperadorDto:
    return DecisionOperadorDto(
        "PL_Manual",
        partida=LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, id_contador=11),
        llegada=LecturaElegidaDto(date(2026, 3, 2), 43_000, 1, id_contador=12),
    )


async def test_pl_manual_se_relee_de_siges_por_id_contador() -> None:
    async def releer(claves: list[tuple[int, str]]) -> _Releidas:
        assert claves == [(6, "10")]
        return {
            (6, "10"): {
                11: LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, id_contador=11),
                12: LecturaElegidaDto(date(2026, 3, 2), 46_000, 1, id_contador=12),
            }
        }

    resultado = await _tablero({(6, "10"): _pl_con_ids()}, releer=releer)

    fila = _fila(resultado, "CD0004MONO")
    # Llegada corregida en Siges: 6.000 en 30 días → 200/día, +59 días.
    assert fila.estim_propuesto == 57_800
    assert resultado.restauracion.restauradas == 1


async def test_pl_manual_con_lectura_borrada_en_siges_se_descarta() -> None:
    async def releer(claves: list[tuple[int, str]]) -> _Releidas:
        return {(6, "10"): {11: LecturaElegidaDto(date(2026, 1, 31), 40_000, 1, id_contador=11)}}

    resultado = await _tablero({(6, "10"): _pl_con_ids()}, releer=releer)

    assert _fila(resultado, "CD0004MONO").fuente == "Parque_Cliente_Tec"
    assert resultado.restauracion.descartadas == 1


async def test_si_falla_la_relectura_se_descarta_esa_pl_y_se_loguea(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def releer(claves: list[tuple[int, str]]) -> _Releidas:
        raise ConnectionError("Siges no responde")

    resultado = await _tablero({(6, "10"): _pl_con_ids()}, releer=releer)

    assert resultado.restauracion.descartadas == 1
    assert "No se pudieron releer los candidatos" in caplog.text


async def test_pl_manual_sin_id_contador_en_modo_real_se_descarta() -> None:
    """`ReconstruirOverrideAsync`: sin `PartidaIdContador`/`LlegadaIdContador`
    no se puede releer la pareja y la decisión no se restaura."""

    async def releer(claves: list[tuple[int, str]]) -> _Releidas:
        raise AssertionError("sin ids no hay nada que releer")

    sin_ids = DecisionOperadorDto(
        "PL_Manual",
        partida=LecturaElegidaDto(date(2026, 1, 31), 40_000, 1),
        llegada=LecturaElegidaDto(date(2026, 3, 2), 43_000, 1),
    )

    resultado = await _tablero({(6, "10"): sin_ids}, releer=releer)

    assert _fila(resultado, "CD0004MONO").fuente == "Parque_Cliente_Tec"
    assert resultado.restauracion.descartadas == 1


async def test_pl_manual_sin_id_contador_en_modo_ejemplo_usa_lo_guardado() -> None:
    """Las lecturas de ejemplo no existen en Siges: sin relectura, la P/L se
    recalcula con los valores guardados."""
    sin_ids = DecisionOperadorDto(
        "PL_Manual",
        partida=LecturaElegidaDto(date(2026, 1, 31), 40_000, 1),
        llegada=LecturaElegidaDto(date(2026, 3, 2), 43_000, 1),
    )

    resultado = await _tablero({(6, "10"): sin_ids})

    fila = _fila(resultado, "CD0004MONO")
    assert (fila.fuente, fila.tipo_toma, fila.editado_por_operador) == ("Historia_Propia", 14, True)
    assert fila.metodo == "EntreReales"
    assert fila.etiqueta_nivel.startswith("Pareja P/L manual · P:31/01/26=40000")


async def test_fila_expone_lo_que_usa_el_tooltip_y_los_bordes_de_la_grilla() -> None:
    resultado = await _tablero()

    t4 = _fila(resultado, "CD0002MONO")
    assert t4.metodo != "NoAplica"
    real = _fila(resultado, "CD0001MONO")
    assert (real.metodo, real.guia_operador, real.t4_sin_revisar) == ("NoAplica", None, False)
    assert real.meses_sin_real_en_alerta is False


async def test_fila_expone_las_lecturas_para_preseleccionar_pl_en_el_panel() -> None:
    """`PanelCandidatos.PreseleccionarPL`: L = UltimoReal, P = RealAnterior."""
    fila = _fila(await _tablero(), "CD0007MONO")

    assert (fila.ultimo_real_fecha, fila.ultimo_real_tipo) == (date(2026, 3, 31), 1)
    assert (fila.real_anterior_fecha, fila.real_anterior_tipo) == (date(2026, 2, 1), 1)


async def test_fila_sin_parque_expone_niveles_vacios_para_el_detalle_historico() -> None:
    fila = _fila(await _tablero(), "CD0007MONO")

    assert fila.parque_historico is not None
    assert fila.parque_historico.cliente_modelo.n == 0
    assert fila.parque_historico.cliente_modelo.p80 is None
