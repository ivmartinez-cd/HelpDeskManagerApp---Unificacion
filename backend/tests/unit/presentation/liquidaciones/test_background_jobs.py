"""Glue de los jobs de fondo de liquidaciones: el loop nunca muere por un ciclo
fallido, respeta el intervalo, el ciclo de reconciliación compone
`SincronizarLiquidaciones` con `permitir_eliminar_anuladas=False` y commitea, y
el de tarifarios aplica el sync de Siges y reanaliza solo si creó algo. Todo
mockeado — acá no se toca wsAyC, Siges, la DB ni nada real."""

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
        monkeypatch.setattr(bj, "build_sincronizar_liquidaciones", lambda s: _FakeSincronizar())

        await bj._ciclo_reconciliar()

        assert llamadas == [{"permitir_eliminar_anuladas": False}]
        assert session.commits == 1


def _resultado_sync(creados: int, conflictos: list[object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        creados=creados,
        sin_cambios=10,
        conflictos=conflictos or [],
        zonas_sin_mapear=[],
        prestadores_sin_vinculo=[],
        prestadores_sin_generica=[],
    )


class TestCicloSyncTarifarios:
    @pytest.mark.asyncio
    async def test_aplica_sync_y_reanaliza_solo_si_creo_algo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        session = _FakeSession()
        llamadas: list[str] = []

        class _FakeSync:
            async def execute(self, **kwargs: object) -> SimpleNamespace:
                llamadas.append(f"sync dry_run={kwargs['dry_run']}")
                return _resultado_sync(creados=6)

        class _FakeReanalizar:
            async def execute(self, prestador_id: object) -> SimpleNamespace:
                llamadas.append(f"reanalizar {prestador_id}")
                return SimpleNamespace(reanalizadas=2, total_alertas=9)

        monkeypatch.setattr(bj, "get_sessionmaker", lambda: lambda: session)
        monkeypatch.setattr(bj, "build_sync_tarifarios_desde_siges", lambda s: _FakeSync())
        monkeypatch.setattr(
            bj, "build_reanalizar_liquidaciones_abiertas", lambda s: _FakeReanalizar()
        )

        await bj._ciclo_sync_tarifarios()

        assert llamadas == ["sync dry_run=False", "reanalizar None"]
        assert session.commits == 1

    @pytest.mark.asyncio
    async def test_sin_creadas_no_reanaliza_y_loguea_conflictos(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        session = _FakeSession()

        class _FakeSync:
            async def execute(self, **kwargs: object) -> SimpleNamespace:
                return _resultado_sync(creados=0, conflictos=[SimpleNamespace(prestador="TUCUMAN")])

        def _no_debe_llamarse(s: object) -> None:
            raise AssertionError("no hay nada nuevo: no corresponde reanalizar")

        monkeypatch.setattr(bj, "get_sessionmaker", lambda: lambda: session)
        monkeypatch.setattr(bj, "build_sync_tarifarios_desde_siges", lambda s: _FakeSync())
        monkeypatch.setattr(bj, "build_reanalizar_liquidaciones_abiertas", _no_debe_llamarse)

        await bj._ciclo_sync_tarifarios()

        assert session.commits == 1
        assert any("conflicto(s) local≠Siges" in r.message for r in caplog.records)


class TestStart:
    @pytest.mark.asyncio
    async def test_crea_un_task_por_job_con_su_intervalo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        arrancados: list[tuple[str, int]] = []

        async def reconciliar(interval_minutes: int) -> None:
            arrancados.append(("reconciliar", interval_minutes))

        async def sync_tarifarios(interval_minutes: int) -> None:
            arrancados.append(("sync_tarifarios", interval_minutes))

        monkeypatch.setattr(bj, "background_liquidaciones_reconciliar_task", reconciliar)
        monkeypatch.setattr(bj, "background_liquidaciones_sync_tarifarios_task", sync_tarifarios)

        tasks = bj.start_liquidaciones_background_jobs(
            interval_minutes=120, sync_tarifarios_interval_minutes=1440
        )
        for t in tasks:
            await t

        assert len(tasks) == 2
        assert arrancados == [("reconciliar", 120), ("sync_tarifarios", 1440)]
