"""Glue del job de Despachados y de "Actualizar ahora": el ciclo respeta la ventana (también
el primero), una corrida fallida o "en curso" no corta el loop, la corrida arma el caso de
uso sobre su propia sesión, y la tarea manual guarda su referencia hasta terminar. Todo
mockeado: acá no se toca ORION, OCA ni la base."""

import asyncio
import logging
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest

import src.modules.insumos.presentation.despachados_jobs as jobs
import src.shared.presentation.app as app_module
from src.modules.insumos.domain.entities.despachados.corrida import OrigenCorrida, ResumenCorrida
from src.modules.insumos.domain.errores_despachados import SincronizacionDespachosEnCursoError
from src.modules.insumos.domain.services.despachados.ventana_job import VentanaJob

_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")
_JUEVES_10 = datetime(2026, 9, 24, 10, 0, tzinfo=_ARGENTINA)
_DOMINGO_10 = datetime(2026, 9, 27, 10, 0, tzinfo=_ARGENTINA)
_JUEVES_21 = datetime(2026, 9, 24, 21, 0, tzinfo=_ARGENTINA)
_VENTANA = VentanaJob(dias_semana=frozenset(range(6)), hora_inicio=8, hora_fin=20)


class _CorteDeLoopError(Exception):
    """Sale del while True del loop desde el sleep fake."""


def _sleep_que_corta(registro: list[float]) -> Any:
    async def _sleep(segundos: float) -> None:
        registro.append(segundos)
        raise _CorteDeLoopError

    return _sleep


def _sincronizar_que(llamadas: list[tuple[Any, ...]], error: Exception | None = None) -> Any:
    async def _sincronizar(origen: OrigenCorrida, usuario: str | None) -> ResumenCorrida:
        llamadas.append((origen, usuario))
        if error is not None:
            raise error
        return ResumenCorrida(envios_nuevos=2, consultas_ok=5)

    return _sincronizar


async def _una_vuelta(monkeypatch: pytest.MonkeyPatch, ahora: datetime) -> list[float]:
    """Corre el loop hasta el primer sleep con `ahora` fijo; devuelve las esperas."""
    esperas: list[float] = []
    monkeypatch.setattr(jobs, "_ahora", lambda: ahora)
    monkeypatch.setattr(asyncio, "sleep", _sleep_que_corta(esperas))
    with pytest.raises(_CorteDeLoopError):
        await jobs._loop(_VENTANA, 120)
    return esperas


class TestLoop:
    @pytest.mark.parametrize("ahora", [_DOMINGO_10, _JUEVES_21])
    async def test_fuera_de_ventana_no_corre_y_lo_loguea(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, ahora: datetime
    ) -> None:
        llamadas: list[tuple[Any, ...]] = []
        monkeypatch.setattr(jobs, "_sincronizar", _sincronizar_que(llamadas))

        with caplog.at_level(logging.INFO, logger=jobs.__name__):
            esperas = await _una_vuelta(monkeypatch, ahora)

        assert llamadas == []
        assert esperas == [7200]
        assert any("fuera de ventana" in r.getMessage() for r in caplog.records)

    async def test_en_ventana_corre_la_programada(self, monkeypatch: pytest.MonkeyPatch) -> None:
        llamadas: list[tuple[Any, ...]] = []
        monkeypatch.setattr(jobs, "_sincronizar", _sincronizar_que(llamadas))

        esperas = await _una_vuelta(monkeypatch, _JUEVES_10)

        assert llamadas == [(OrigenCorrida.PROGRAMADA, None)]
        assert esperas == [7200]

    async def test_error_se_loguea_con_traza_y_no_corta_el_loop(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        llamadas: list[tuple[Any, ...]] = []
        monkeypatch.setattr(jobs, "_sincronizar", _sincronizar_que(llamadas, RuntimeError("x")))

        esperas = await _una_vuelta(monkeypatch, _JUEVES_10)

        assert esperas == [7200]
        errores = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(errores) == 1 and errores[0].exc_info is not None

    async def test_corrida_en_curso_se_loguea_como_info(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        error = SincronizacionDespachosEnCursoError()
        monkeypatch.setattr(jobs, "_sincronizar", _sincronizar_que([], error))

        with caplog.at_level(logging.INFO, logger=jobs.__name__):
            esperas = await _una_vuelta(monkeypatch, _JUEVES_10)

        assert esperas == [7200]
        assert any("en curso" in r.getMessage() for r in caplog.records)
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


class _FakeSession:
    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


async def test_sincronizar_arma_el_caso_de_uso_sobre_una_sesion_propia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession()
    recibido: list[Any] = []

    class _FakeSincronizar:
        async def execute(self, origen: OrigenCorrida, usuario: str | None) -> ResumenCorrida:
            recibido.append((origen, usuario))
            return ResumenCorrida()

    def _build(sesion: Any) -> _FakeSincronizar:
        recibido.append(sesion)
        return _FakeSincronizar()

    monkeypatch.setattr(jobs, "get_sessionmaker", lambda: lambda: session)
    monkeypatch.setattr(jobs, "build_sincronizar_despachos", _build)

    await jobs._sincronizar(OrigenCorrida.MANUAL, "Ana")

    assert recibido == [session, (OrigenCorrida.MANUAL, "Ana")]


async def test_actualizacion_manual_guarda_y_libera_su_referencia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[tuple[Any, ...]] = []
    monkeypatch.setattr(jobs, "_sincronizar", _sincronizar_que(llamadas))

    jobs.lanzar_actualizacion_manual("Ana")
    (tarea,) = jobs._tareas_manuales
    await tarea
    await asyncio.sleep(0)  # deja correr el done_callback

    assert llamadas == [(OrigenCorrida.MANUAL, "Ana")]
    assert jobs._tareas_manuales == set()


def _settings(**cambios: Any) -> Any:
    base = {
        "disable_despachados_background_jobs": False,
        "despachados_dias_semana": (0, 1, 2, 3, 4, 5),
        "despachados_hora_inicio": 8,
        "despachados_hora_fin": 20,
        "despachados_intervalo_minutos": 120,
    }
    return SimpleNamespace(**{**base, **cambios})


def test_ventana_desde_settings_y_ventana_invalida_falla_al_arrancar() -> None:
    assert jobs.ventana_desde(_settings()) == _VENTANA
    with pytest.raises(ValueError):
        jobs.ventana_desde(_settings(despachados_hora_inicio=20))


class TestRegistroEnApp:
    def test_flag_encendido_omite_despachados_y_lo_loguea(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr(jobs, "start_despachados_background_jobs", _no_deberia_arrancar)

        with caplog.at_level(logging.INFO, logger=app_module.__name__):
            tareas = app_module._jobs_despachados(
                _settings(disable_despachados_background_jobs=True)
            )

        assert tareas == []
        assert any("despachados omitido" in r.getMessage() for r in caplog.records)

    def test_flag_apagado_arranca_el_job(self, monkeypatch: pytest.MonkeyPatch) -> None:
        centinela: list[Any] = [object()]
        monkeypatch.setattr(jobs, "start_despachados_background_jobs", lambda _s: centinela)

        assert app_module._jobs_despachados(_settings()) is centinela


def _no_deberia_arrancar(_settings: Any) -> list[Any]:
    raise AssertionError("con el flag encendido no se arranca el job")
