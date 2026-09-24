"""Tests de SincronizarDespachos ante errores (de Siges, de OCA e inesperados), con el
candado ocupado, y del calendario de feriados con que se clasifica."""

import logging
from datetime import UTC, date, datetime, timedelta

import pytest

from src.modules.insumos.domain.entities.despachados.corrida import ResumenCorrida
from src.modules.insumos.domain.entities.despachados.envio_seguido import ErrorConsulta
from src.modules.insumos.domain.errores_despachados import SincronizacionDespachosEnCursoError
from src.shared.domain.errors import ExternalServiceError
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    GUIA_A,
    GUIA_B,
    HOY,
    envio,
    estado_oca,
)
from tests.unit.application.insumos.despachados.fakes_sincronizacion import (
    MundoSincronizacion,
    mensajes_de_log,
)


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
        fallos = mensajes_de_log(caplog, "falló la consulta a OCA")
        assert len(fallos) == 1
        assert GUIA_A in fallos[0]

    async def test_un_error_de_oca_actualiza_y_confirma_la_guia_antes_de_seguir(self) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B)])
        mundo.oca.respuestas = {GUIA_A: ExternalServiceError("timeout"), GUIA_B: estado_oca(GUIA_B)}

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

    async def test_un_error_inesperado_revierte_lo_no_confirmado_antes_de_terminar(
        self,
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio(GUIA_A), envio(GUIA_B)])
        mundo.oca.respuestas = {GUIA_B: RuntimeError("se rompió")}

        with pytest.raises(RuntimeError, match="se rompió"):
            await mundo.correr()

        assert mundo.eventos[-4:] == [
            f"oca {GUIA_B}",
            "revertir",
            "terminar corrida 1",
            "confirmar",
        ]
        assert mundo.eventos.count("revertir") == 1

    async def test_si_no_puede_terminar_la_corrida_relanza_el_error_original(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        mundo = MundoSincronizacion(envios=[envio()])
        mundo.oca.respuestas = {GUIA_A: RuntimeError("se rompió")}
        mundo.corridas.error_al_terminar = ConnectionError("sin base")

        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match="se rompió"):
            await mundo.correr()

        assert mensajes_de_log(caplog, "no se pudo registrar el final")


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

        avisos = mensajes_de_log(caplog, "feriados cargados")
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

        avisos = mensajes_de_log(caplog, "feriados cargados")
        assert len(avisos) == 1
        assert "2027" in avisos[0]
