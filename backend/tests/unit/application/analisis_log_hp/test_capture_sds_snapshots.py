"""CaptureSdsSnapshots: un snapshot automático por serial trackeado, con
telemetría (bug legacy corregido) y tolerancia a fallas por equipo."""

import pytest

from src.modules.analisis_log_hp.application.use_cases.capture_sds_snapshots import (
    CaptureSdsSnapshots,
)
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import EventLogsResult
from tests.unit.application.analisis_log_hp.fake_gateways import FakeHpPortalGateway
from tests.unit.application.analisis_log_hp.fakes import (
    FakeErrorCodeRepo,
    FakeSavedAnalysisRepo,
    FakeTelemetryRepo,
)

_TSV = (
    "Tipo\tCódigo\tFecha\tContador\tFirmware\tAyuda\n"
    "Error\t13.20.01\t05-ago-2026 09:05:00\t100\tFW\t\n"
    "Error\t13.20.01\t05-ago-2026 10:05:00\t120\tFW\t\n"
)
_HELP = {"13.20.01": {"url": "http://h/13", "description": "Atasco"}}


def _caso(
    portal: FakeHpPortalGateway, *, serials: list[str | None], fail_bulk: bool = False
) -> tuple[CaptureSdsSnapshots, FakeSavedAnalysisRepo, FakeTelemetryRepo, FakeErrorCodeRepo]:
    repo, tele, codes = FakeSavedAnalysisRepo(), FakeTelemetryRepo(), FakeErrorCodeRepo(
        fail_bulk=fail_bulk
    )
    for s in serials:
        repo.seed(equipment_identifier=s)
    return CaptureSdsSnapshots(repo, tele, codes, portal), repo, tele, codes


class TestCaptureSdsSnapshots:
    async def test_crea_snapshot_auto_y_telemetria_por_serial_unico(self) -> None:
        portal = FakeHpPortalGateway(logs=EventLogsResult(tsv=_TSV, help_urls=_HELP))
        uc, repo, tele, codes = _caso(portal, serials=["ser1", "ser1", None])

        results = await uc.execute_all()

        assert len(results) == 1
        r = results[0]
        assert (r.serial, r.skipped, r.incidents_count, r.error) == ("ser1", False, 1, None)
        auto = repo.rows[next(k for k in repo.rows if str(k) == r.snapshot_id)]
        assert auto.name.startswith("Auto - ser1 - ")
        assert auto.name.endswith(("(mañana)", "(tarde)"))
        assert auto.incidents[0]["occurrences"] == 2
        assert [e.device_serial for e in tele.events] == ["ser1"]
        assert tele.events[0].counter == 120
        assert codes.bulk_updates == [_HELP]
        assert ("search_device", "SER1") in portal.calls
        assert ("refresh_hp_cache", "777") in portal.calls

    async def test_sin_incidentes_se_saltea(self) -> None:
        portal = FakeHpPortalGateway(logs=EventLogsResult(tsv=""))
        uc, repo, tele, _ = _caso(portal, serials=["ser1"])
        results = await uc.execute_all()
        assert results[0].skipped is True
        assert len(repo.rows) == 1
        assert tele.events == []

    async def test_falla_del_catalogo_no_frena_la_captura(self) -> None:
        portal = FakeHpPortalGateway(logs=EventLogsResult(tsv=_TSV, help_urls=_HELP))
        uc, _, tele, _ = _caso(portal, serials=["ser1"], fail_bulk=True)
        results = await uc.execute_all()
        assert results[0].error is None
        assert len(tele.events) == 1

    async def test_falla_del_portal_se_reporta_sin_propagar(self) -> None:
        portal = FakeHpPortalGateway(search_error=RuntimeError("portal caído"))
        uc, _, _, _ = _caso(portal, serials=["ser1", "ser2"])
        results = await uc.execute_all()
        assert [r.error for r in results] == ["portal caído", "portal caído"]
        assert all(r.skipped is False for r in results)

    @pytest.mark.parametrize("serials", [[], [None]])
    async def test_sin_seriales_no_hace_nada(self, serials: list[str | None]) -> None:
        portal = FakeHpPortalGateway()
        uc, _, _, _ = _caso(portal, serials=serials)
        assert await uc.execute_all() == []
        assert portal.calls == []
