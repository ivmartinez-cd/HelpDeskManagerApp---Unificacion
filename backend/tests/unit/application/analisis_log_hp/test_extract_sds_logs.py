"""ExtractSdsLogs: serial → device_id + modelo (con fallback a Insight) + TSV,
actualizando el catálogo con las URLs de ayuda."""

from src.modules.analisis_log_hp.application.use_cases.extract_sds_logs import ExtractSdsLogs
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import EventLogsResult
from tests.unit.application.analisis_log_hp.fake_gateways import (
    FakeHpInsightGateway,
    FakeHpPortalGateway,
)
from tests.unit.application.analisis_log_hp.fakes import FakeErrorCodeRepo

_HELP = {"13.20": {"url": "http://h", "description": "Atasco"}}


class TestExtractSdsLogs:
    async def test_usa_el_modelo_del_portal_y_actualiza_catalogo(self) -> None:
        portal = FakeHpPortalGateway(logs=EventLogsResult(tsv="tsv", help_urls=_HELP))
        repo, insight = FakeErrorCodeRepo(), FakeHpInsightGateway()

        result = await ExtractSdsLogs(portal, repo, insight).execute(" abc1 ", days=7)

        assert (result.device_id, result.model_name, result.tsv) == ("777", "HP M404", "tsv")
        assert result.help_urls_updated == 1
        assert repo.bulk_updates == [_HELP]
        assert ("search_device", "ABC1") in portal.calls
        assert ("fetch_event_logs", ("777", 7)) in portal.calls
        assert insight.calls == []

    async def test_sin_help_urls_no_toca_el_catalogo(self) -> None:
        portal = FakeHpPortalGateway(logs=EventLogsResult(tsv="tsv"))
        repo = FakeErrorCodeRepo()
        result = await ExtractSdsLogs(portal, repo, FakeHpInsightGateway()).execute("s")
        assert result.help_urls_updated == 0
        assert repo.bulk_updates == []

    async def test_falla_del_catalogo_no_frena_la_extraccion(self) -> None:
        portal = FakeHpPortalGateway(logs=EventLogsResult(tsv="tsv", help_urls=_HELP))
        repo = FakeErrorCodeRepo(fail_bulk=True)
        result = await ExtractSdsLogs(portal, repo, FakeHpInsightGateway()).execute("s")
        assert (result.tsv, result.help_urls_updated) == ("tsv", 0)

    async def test_modelo_generico_cae_a_insight(self) -> None:
        portal = FakeHpPortalGateway(device={"id": "1", "model_name": "Generico / Desconocido"})
        insight = FakeHpInsightGateway(device={"extendedFields": {"model": "LaserJet E52645"}})
        result = await ExtractSdsLogs(portal, FakeErrorCodeRepo(), insight).execute("s")
        assert result.model_name == "LaserJet E52645"
        assert insight.calls == [("search_by_serial", "S")]

    async def test_insight_sin_modelo_conserva_el_generico(self) -> None:
        portal = FakeHpPortalGateway(device={"id": "1", "model_name": "Generico / Desconocido"})
        insight = FakeHpInsightGateway(device=None)
        result = await ExtractSdsLogs(portal, FakeErrorCodeRepo(), insight).execute("s")
        assert result.model_name == "Generico / Desconocido"

    async def test_portal_sin_modelo_e_insight_caido_devuelve_generico(self) -> None:
        portal = FakeHpPortalGateway(device={"id": "1"})
        insight = FakeHpInsightGateway(search_error=RuntimeError("insight caído"))
        result = await ExtractSdsLogs(portal, FakeErrorCodeRepo(), insight).execute("s")
        assert result.model_name == "Generico / Desconocido"

    async def test_portal_con_modelo_vacio_e_insight_caido_devuelve_generico(self) -> None:
        portal = FakeHpPortalGateway(device={"id": "1", "model_name": ""})
        insight = FakeHpInsightGateway(search_error=RuntimeError("insight caído"))
        result = await ExtractSdsLogs(portal, FakeErrorCodeRepo(), insight).execute("s")
        assert result.model_name == "Generico / Desconocido"
