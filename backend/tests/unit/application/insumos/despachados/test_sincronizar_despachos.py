"""Tests de SincronizarDespachos: alta desde Siges, consulta a OCA de los abiertos, orden de
las escrituras y confirmaciones, historial y alertas. Los errores, el candado y los feriados
están en `test_sincronizar_despachos_errores.py`."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import date, timedelta

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
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.shared.domain.errors import ExternalServiceError
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    CONFIG,
    GUIA_A,
    GUIA_B,
    GUIA_C,
    VERDE,
    despacho,
    envio,
    estado_oca,
)
from tests.unit.application.insumos.despachados.fakes_sincronizacion import (
    MundoSincronizacion,
    mensajes_de_log,
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

    async def test_actualiza_y_confirma_cada_guia_antes_de_seguir(self) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B)])

        await mundo.correr()

        assert mundo.eventos == [
            "confirmar",  # corrida iniciada
            "confirmar",  # guías y remitos de Siges
            f"oca {GUIA_A}",
            f"actualizar {GUIA_A}",
            "confirmar",
            "pausa 0.3",
            f"oca {GUIA_B}",
            f"actualizar {GUIA_B}",
            "confirmar",
            "terminar corrida 1",
            "confirmar",
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

    @pytest.mark.parametrize(
        ("dias_sin_movimiento", "color"),
        [(3, ColorSemaforo.VERDE), (1, ColorSemaforo.AMARILLO)],
    )
    async def test_los_dias_sin_movimiento_salen_de_la_configuracion(
        self, dias_sin_movimiento: int, color: ColorSemaforo
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio()])
        mundo.oca.respuestas = {GUIA_A: estado_oca()}  # 1 día hábil sin movimiento
        config = replace(CONFIG, dias_sin_movimiento=dias_sin_movimiento)

        await mundo.caso_de_uso(config).execute(OrigenCorrida.PROGRAMADA)

        assert mundo.envios.envios[GUIA_A].clasificacion.color is color

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

        avisos = mensajes_de_log(caplog, "fuera del catálogo")
        assert len(avisos) == 1
        assert GUIA_A in avisos[0]
        assert "999" in avisos[0]
        assert "Estado raro" in avisos[0]
