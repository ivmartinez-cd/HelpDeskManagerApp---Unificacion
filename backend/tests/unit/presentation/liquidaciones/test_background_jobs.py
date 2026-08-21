"""Glue del job de fondo de liquidaciones: el loop nunca muere por un ciclo
fallido, respeta el intervalo, el ciclo compone `SincronizarLiquidaciones` con
`permitir_eliminar_anuladas=False` y commitea. Todo mockeado — acá no se toca
wsAyC, la DB ni nada real."""

from types import SimpleNamespace
from typing import Any

import pytest

import src.modules.liquidaciones.presentation.background_jobs as bj


class _CorteDeLoopError(Exception):
    """Sale del while True del loop desde el sleep fake."""


def _sleep_que_corta(registro: list[float]) -> Any:
    async def _sleep(segundos: float) -> None:
        registro.append(segundos)
        raise _CorteDeLoopError

    return _sleep


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


class TestLoop:
    @pytest.mark.asyncio
    async def test_ciclo_ok_y_luego_duerme_el_intervalo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        llamadas: list[int] = []
        esperas: list[float] = []

        async def ciclo() -> None:
            llamadas.append(1)

        monkeypatch.setattr(bj.asyncio, "sleep", _sleep_que_corta(esperas))
        with pytest.raises(_CorteDeLoopError):
            await bj._loop("test_job", ciclo, interval_minutes=5)
        assert llamadas == [1]
        assert esperas == [300]

    @pytest.mark.asyncio
    async def test_ciclo_fallido_se_loguea_y_no_corta_el_loop(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        esperas: list[float] = []

        async def ciclo() -> None:
            raise ValueError("wsAyC caído")

        monkeypatch.setattr(bj.asyncio, "sleep", _sleep_que_corta(esperas))
        with pytest.raises(_CorteDeLoopError):
            await bj._loop("test_job", ciclo, interval_minutes=1)
        assert esperas == [60]
        assert any("ciclo fallido" in r.message for r in caplog.records)


class TestCicloReconciliar:
    @pytest.mark.asyncio
    async def test_compone_ejecuta_sin_borrar_anuladas_y_commitea(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeSession()
        llamadas: list[dict[str, object]] = []

        class _FakeSincronizar:
            async def execute(self, **kwargs: object) -> SimpleNamespace:
                llamadas.append(kwargs)
                return SimpleNamespace(
                    creadas=0,
                    reconciliadas=5,
                    estados_actualizados=2,
                    extras_actualizados=1,
                    facturas_actualizadas=1,
                    fallidas=0,
                )

        monkeypatch.setattr(bj, "get_sessionmaker", lambda: lambda: session)
        monkeypatch.setattr(
            bj, "build_sincronizar_liquidaciones", lambda s: _FakeSincronizar()
        )

        await bj._ciclo_reconciliar()

        assert llamadas == [{"permitir_eliminar_anuladas": False}]
        assert session.commits == 1


class TestStart:
    @pytest.mark.asyncio
    async def test_crea_un_task_con_su_intervalo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        arrancados: list[tuple[str, int]] = []

        async def reconciliar(interval_minutes: int) -> None:
            arrancados.append(("reconciliar", interval_minutes))

        monkeypatch.setattr(bj, "background_liquidaciones_reconciliar_task", reconciliar)

        tasks = bj.start_liquidaciones_background_jobs(interval_minutes=120)
        for t in tasks:
            await t

        assert len(tasks) == 1
        assert arrancados == [("reconciliar", 120)]
