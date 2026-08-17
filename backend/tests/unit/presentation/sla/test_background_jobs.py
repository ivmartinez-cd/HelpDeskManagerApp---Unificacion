"""Glue de los jobs de fondo de sla: el loop nunca muere por un ciclo fallido,
respeta el intervalo, y cada ciclo compone sus dependencias y commitea.
Todo mockeado — acá no se toca Mercurio, la DB ni nada real."""

from types import SimpleNamespace
from typing import Any

import pytest

import src.modules.sla.presentation.background_jobs as bj


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
            raise ValueError("mercurio caído")

        monkeypatch.setattr(bj.asyncio, "sleep", _sleep_que_corta(esperas))
        # La excepción del ciclo NO propaga: el loop la traga y llega al sleep.
        with pytest.raises(_CorteDeLoopError):
            await bj._loop("test_job", ciclo, interval_minutes=1)
        assert esperas == [60]
        assert any("ciclo fallido" in r.message for r in caplog.records)


class TestCicloSla:
    @pytest.mark.asyncio
    async def test_compone_ejecuta_y_commitea(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeSession()
        ejecutados: list[int] = []

        class _FakeRefresh:
            def __init__(self, gateway: object, repo: object) -> None:
                pass

            async def execute(self, periodo: int) -> SimpleNamespace:
                ejecutados.append(periodo)
                return SimpleNamespace(periodo=periodo, total=10, vencidos=2)

        monkeypatch.setattr(bj, "get_sessionmaker", lambda: lambda: session)
        monkeypatch.setattr(bj, "get_sla_query_gateway", lambda: object())
        monkeypatch.setattr(bj, "SqlAlchemySlaSnapshotRepository", lambda s: object())
        monkeypatch.setattr(bj, "RefreshSlaSnapshot", _FakeRefresh)

        await bj._ciclo_sla()
        assert ejecutados == [bj._periodo_actual()]
        assert session.commits == 1


class TestCicloPendientes:
    @pytest.mark.asyncio
    async def test_compone_ejecuta_y_commitea(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeSession()
        cortes: list[int] = []

        class _FakeRefresh:
            def __init__(
                self, gateway: object, repo: object, *, pst_lookup: object, meses_corte: int
            ) -> None:
                cortes.append(meses_corte)

            async def execute(self) -> SimpleNamespace:
                return SimpleNamespace(total=7, por_prestador=["A", "B"])

        monkeypatch.setattr(bj, "get_settings", lambda: SimpleNamespace(pendientes_meses_corte=24))
        monkeypatch.setattr(bj, "get_sessionmaker", lambda: lambda: session)
        monkeypatch.setattr(bj, "get_pendientes_query_gateway", lambda: object())
        monkeypatch.setattr(bj, "SqlAlchemyPendientesSnapshotRepository", lambda s: object())
        monkeypatch.setattr(bj, "SqlAlchemyPrestadorLookup", lambda s: object())
        monkeypatch.setattr(bj, "RefreshPendientesSnapshot", _FakeRefresh)

        await bj._ciclo_pendientes()
        assert cortes == [24]
        assert session.commits == 1


class TestStart:
    @pytest.mark.asyncio
    async def test_crea_los_dos_tasks_con_sus_intervalos(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        arrancados: list[tuple[str, int]] = []

        async def sla(interval_minutes: int) -> None:
            arrancados.append(("sla", interval_minutes))

        async def pendientes(interval_minutes: int) -> None:
            arrancados.append(("pendientes", interval_minutes))

        monkeypatch.setattr(bj, "background_sla_refresh_task", sla)
        monkeypatch.setattr(bj, "background_pendientes_refresh_task", pendientes)
        monkeypatch.setattr(
            bj, "get_settings", lambda: SimpleNamespace(pendientes_refresh_interval_minutes=60)
        )

        tasks = bj.start_sla_background_jobs(interval_minutes=240)
        for t in tasks:
            await t
        assert len(tasks) == 2
        assert sorted(arrancados) == [("pendientes", 60), ("sla", 240)]
