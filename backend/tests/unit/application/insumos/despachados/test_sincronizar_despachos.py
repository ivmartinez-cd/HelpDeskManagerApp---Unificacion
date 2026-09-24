"""Tests de SincronizarDespachos: alta desde Siges, consulta a OCA de los abiertos, errores
que no cortan el lote, candado y registro de la corrida."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from src.modules.insumos.application.use_cases.despachados.sincronizar_despachos import (
    MOTIVO_INTERRUMPIDA,
)
from src.modules.insumos.domain.entities.despachados.corrida import (
    Corrida,
    OrigenCorrida,
    ResumenCorrida,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    ErrorConsulta,
)
from src.modules.insumos.domain.errores_despachados import SincronizacionDespachosEnCursoError
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.shared.domain.errors import ExternalServiceError
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    GUIA_A,
    GUIA_B,
    GUIA_C,
    HOY,
    VERDE,
    MundoSincronizacion,
    despacho,
    envio,
    estado_oca,
)

NARANJA = replace(VERDE, color=ColorSemaforo.NARANJA, alerta=True)
ROJO = replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 29))
"""Un 45 con `FechaEstado` el miércoles 23/09/2026."""
CIERRE = CierreAlerta(
    cerrada_en=AHORA - timedelta(hours=1), usuario_id=None, usuario_nombre="Ana Operadora"
)
EN_ESPERA = estado_oca(id_estado=45, estado="En Espera de Retiro por Sucursal")
COLGADA = Corrida(1, OrigenCorrida.PROGRAMADA, AHORA - timedelta(hours=3), None)
"""Una corrida que quedó sin terminar porque el proceso se reinició."""


def _eventos_oca(mundo: MundoSincronizacion) -> list[str]:
    return [e for e in mundo.eventos if e.startswith(("oca", "pausa"))]


def _mensajes(caplog: pytest.LogCaptureFixture, texto: str) -> list[str]:
    return [r.getMessage() for r in caplog.records if texto in r.getMessage()]


def _operador_cierra_la_alerta(mundo: MundoSincronizacion) -> Callable[[str], Awaitable[None]]:
    """Mientras OCA contesta, un operador cierra la alerta de la guía (otro request)."""

    async def cerrar(guia: str) -> None:
        actual = mundo.envios.envios[guia]
        mundo.envios.envios[guia] = replace(actual, cierre_alerta=CIERRE)

    return cerrar


class TestCaminoFeliz:
    async def test_da_de_alta_las_guias_nuevas_y_consulta_los_abiertos(self) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_B)])
        mundo.siges.despachos = [
            despacho(GUIA_A, 1, fecha_remito=date(2026, 9, 23), cliente="Remito nuevo"),
            despacho(GUIA_A, 2, fecha_remito=date(2026, 9, 22), cliente="Remito viejo"),
            despacho(GUIA_B, 3),
        ]
        mundo.oca.respuestas = {GUIA_A: estado_oca(GUIA_A), GUIA_B: estado_oca(GUIA_B)}

        resumen = await mundo.correr()

        assert resumen == ResumenCorrida(envios_nuevos=1, consultas_ok=2, consultas_error=0)
        assert [(e.guia, e.cliente) for e in mundo.envios.creados] == [(GUIA_A, "Remito viejo")]
        assert mundo.remitos.guardados == mundo.siges.despachos
        assert mundo.siges.llamadas == [(30, (3, 9, 10))]
        assert mundo.envios.envios[GUIA_A].estado_oca == estado_oca(GUIA_A)
        assert mundo.envios.envios[GUIA_A].consultado_en == AHORA
        assert [guia for guia, _, _ in mundo.historial.registros] == [GUIA_A, GUIA_B]
        assert mundo.corridas.terminadas == {1: resumen}

    async def test_confirma_despues_de_cada_paso(self) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B)])

        await mundo.correr()

        assert mundo.eventos == [
            "confirmar",  # corrida iniciada
            "confirmar",  # guías y remitos de Siges
            f"oca {GUIA_A}",
            "confirmar",
            "pausa 0.3",
            f"oca {GUIA_B}",
            "confirmar",
            "confirmar",  # corrida terminada
        ]

    async def test_registra_origen_y_usuario_de_una_corrida_manual(self) -> None:
        mundo = MundoSincronizacion()

        await mundo.caso_de_uso().execute(OrigenCorrida.MANUAL, "Ana Operadora")

        corrida = mundo.corridas.iniciadas[0]
        assert (corrida.origen, corrida.usuario_nombre) == (OrigenCorrida.MANUAL, "Ana Operadora")

    async def test_los_remitos_de_una_guia_nueva_se_guardan_despues_de_su_envio(self) -> None:
        mundo = MundoSincronizacion()
        mundo.siges.despachos = [despacho(GUIA_A, 1), despacho(GUIA_A, 2)]

        resumen = await mundo.correr()

        assert resumen.error is None
        assert GUIA_A in mundo.envios.envios
        assert mundo.remitos.guardados == mundo.siges.despachos

    async def test_cierra_las_colgadas_como_interrumpidas_pero_no_la_que_inicia(self) -> None:
        mundo = MundoSincronizacion(envios=[envio()])
        mundo.corridas.iniciadas.append(COLGADA)
        vistas: list[Corrida | None] = []

        async def mirar_la_ultima_corrida(guia: str) -> None:
            vistas.append(await mundo.corridas.ultima())

        mundo.oca.al_responder = mirar_la_ultima_corrida

        resumen = await mundo.correr()

        [en_curso] = vistas
        assert en_curso is not None
        assert (en_curso.id, en_curso.terminada_en) == (2, None)
        assert mundo.corridas.terminadas == {
            1: ResumenCorrida(error=MOTIVO_INTERRUMPIDA),
            2: resumen,
        }

    async def test_pausa_solo_entre_consultas(self) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B), envio(GUIA_C)])

        await mundo.correr()

        assert _eventos_oca(mundo) == [
            f"oca {GUIA_A}",
            "pausa 0.3",
            f"oca {GUIA_B}",
            "pausa 0.3",
            f"oca {GUIA_C}",
        ]

    async def test_no_consulta_los_envios_cerrados(self) -> None:
        cerrado = envio(GUIA_B, clasificacion=replace(VERDE, abierto=False))
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), cerrado])

        await mundo.correr()

        assert _eventos_oca(mundo) == [f"oca {GUIA_A}"]


class TestHistorialYAlertas:
    async def test_el_historial_solo_registra_cambios_de_estado(self) -> None:
        igual = estado_oca(GUIA_A, estado="  EN VIAJE a centro de distribucion de destino")
        mundo = MundoSincronizacion(
            envios=[envio(GUIA_A, estado_oca=estado_oca(GUIA_A)), envio(GUIA_B)]
        )
        mundo.oca.respuestas = {GUIA_A: igual, GUIA_B: EN_ESPERA}

        await mundo.correr()

        assert mundo.historial.registros == [(GUIA_B, EN_ESPERA, ColorSemaforo.ROJO)]
        assert mundo.envios.envios[GUIA_A].estado_oca == igual

    async def test_un_cambio_de_estado_con_alerta_reabre_la_alerta_cerrada(self) -> None:
        visita_fallida = estado_oca(id_estado=48, estado="Reprogramado", motivo="No Responde")
        mundo = MundoSincronizacion(
            envios=[envio(estado_oca=visita_fallida, clasificacion=NARANJA, cierre_alerta=CIERRE)]
        )
        mundo.oca.respuestas = {GUIA_A: EN_ESPERA}

        await mundo.correr()

        actualizado = mundo.envios.envios[GUIA_A]
        assert (actualizado.clasificacion, actualizado.cierre_alerta) == (ROJO, None)
        assert actualizado.alerta_abierta is True

    async def test_no_pisa_un_cierre_de_alerta_registrado_durante_la_corrida(self) -> None:
        mundo = MundoSincronizacion(envios=[envio(estado_oca=EN_ESPERA, clasificacion=ROJO)])
        mundo.oca.respuestas = {GUIA_A: EN_ESPERA}
        mundo.oca.al_responder = _operador_cierra_la_alerta(mundo)

        await mundo.correr()

        assert mundo.envios.envios[GUIA_A].cierre_alerta == CIERRE
        assert mundo.envios.envios[GUIA_A].consultado_en == AHORA

    async def test_un_fallo_de_oca_tampoco_pisa_un_cierre_registrado_durante_la_corrida(
        self,
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio(estado_oca=EN_ESPERA, clasificacion=ROJO)])
        mundo.oca.respuestas = {GUIA_A: ExternalServiceError("timeout")}
        mundo.oca.al_responder = _operador_cierra_la_alerta(mundo)

        resumen = await mundo.correr()

        con_error = mundo.envios.envios[GUIA_A]
        assert con_error.cierre_alerta == CIERRE
        assert con_error.ultimo_error == ErrorConsulta(mensaje="timeout", ocurrido_en=AHORA)
        assert resumen.consultas_error == 1

    async def test_un_estado_desconocido_se_loguea_con_la_guia(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio()])
        mundo.oca.respuestas = {GUIA_A: estado_oca(id_estado=999, estado="Estado raro")}

        with caplog.at_level(logging.WARNING):
            await mundo.correr()

        avisos = _mensajes(caplog, "fuera del catálogo")
        assert len(avisos) == 1
        assert GUIA_A in avisos[0]
        assert "999" in avisos[0]
        assert "Estado raro" in avisos[0]


class TestErrores:
    async def test_un_error_de_oca_no_corta_el_lote_y_queda_registrado(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B)])
        mundo.oca.respuestas = {GUIA_A: ExternalServiceError("timeout"), GUIA_B: estado_oca(GUIA_B)}

        with caplog.at_level(logging.WARNING):
            resumen = await mundo.correr()

        assert resumen == ResumenCorrida(consultas_ok=1, consultas_error=1)
        con_error = mundo.envios.envios[GUIA_A]
        assert con_error.ultimo_error == ErrorConsulta(mensaje="timeout", ocurrido_en=AHORA)
        assert con_error.consultado_en is None
        assert mundo.envios.envios[GUIA_B].estado_oca == estado_oca(GUIA_B)
        fallos = _mensajes(caplog, "falló la consulta a OCA")
        assert len(fallos) == 1
        assert GUIA_A in fallos[0]

    async def test_con_siges_caido_igual_consulta_los_abiertos(self) -> None:
        mundo = MundoSincronizacion(envios=[envio()])
        mundo.siges.error = ExternalServiceError("Siges no responde")
        mundo.oca.respuestas = {GUIA_A: estado_oca()}

        resumen = await mundo.correr()

        assert resumen == ResumenCorrida(
            consultas_ok=1, error="No se pudo leer Siges: Siges no responde"
        )
        assert mundo.remitos.guardados == []
        assert mundo.envios.envios[GUIA_A].estado_oca == estado_oca()
        assert mundo.corridas.terminadas == {1: resumen}

    async def test_con_el_candado_ocupado_no_toca_nada(self) -> None:
        mundo = MundoSincronizacion(envios=[envio()], candado_libre=False)

        with pytest.raises(SincronizacionDespachosEnCursoError):
            await mundo.correr()

        assert mundo.corridas.interrumpidas == []
        assert mundo.corridas.iniciadas == []
        assert mundo.siges.llamadas == []
        assert mundo.eventos == []

    async def test_un_error_inesperado_termina_la_corrida_con_el_error_y_se_relanza(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B)])
        mundo.oca.respuestas = {GUIA_B: RuntimeError("se rompió")}

        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match="se rompió"):
            await mundo.correr()

        assert mundo.corridas.terminadas == {
            1: ResumenCorrida(consultas_ok=1, error="RuntimeError: se rompió")
        }
        assert any(r.exc_info is not None for r in caplog.records)

    async def test_si_no_puede_terminar_la_corrida_relanza_el_error_original(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio()])
        mundo.oca.respuestas = {GUIA_A: RuntimeError("se rompió")}
        mundo.corridas.error_al_terminar = ConnectionError("sin base")

        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match="se rompió"):
            await mundo.correr()

        assert _mensajes(caplog, "no se pudo registrar el final")


class TestFeriados:
    async def test_pide_feriados_de_400_dias_atras_a_60_adelante(self) -> None:
        mundo = MundoSincronizacion()

        await mundo.correr()

        assert mundo.feriados.consultas == [(HOY - timedelta(400), HOY + timedelta(60))]

    async def test_hoy_es_la_fecha_argentina(self) -> None:
        mundo = MundoSincronizacion()
        mundo.ahora = datetime(2026, 9, 25, 2, 0, tzinfo=UTC)  # 24/09 23:00 en Argentina

        await mundo.correr()

        assert mundo.feriados.consultas[0][1] == HOY + timedelta(60)

    async def test_avisa_si_el_anio_no_tiene_feriados_cargados(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion()
        mundo.feriados.feriados = frozenset()

        with caplog.at_level(logging.WARNING):
            await mundo.correr()

        avisos = _mensajes(caplog, "feriados cargados")
        assert len(avisos) == 1
        assert "2026" in avisos[0]

    async def test_cerca_de_fin_de_anio_avisa_por_el_anio_siguiente(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion()
        mundo.ahora = datetime(2026, 12, 10, 15, 0, tzinfo=UTC)
        mundo.feriados.feriados = frozenset({date(2026, 12, 8), date(2026, 12, 25)})

        with caplog.at_level(logging.WARNING):
            await mundo.correr()

        avisos = _mensajes(caplog, "feriados cargados")
        assert len(avisos) == 1
        assert "2027" in avisos[0]
