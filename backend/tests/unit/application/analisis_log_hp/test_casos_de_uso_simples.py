"""Casos de uso delgados: IA (costo), CPMD, Insight en vivo, portal SDS
(operaciones/EWS/caché/solución) y upsert del catálogo."""

import pytest

from src.modules.analisis_log_hp.application.use_cases.cpmd import (
    FindCpmdManual,
    GetCpmdManualById,
    UploadCpmdManual,
)
from src.modules.analisis_log_hp.application.use_cases.diagnose_ai import (
    DiagnoseAi,
    GeneratePdfSummary,
    _cost,
)
from src.modules.analisis_log_hp.application.use_cases.get_device_live_data import (
    GetClientDevices,
    GetClients,
    GetDeviceAlerts,
    GetDeviceConsumables,
    GetDeviceMeters,
)
from src.modules.analisis_log_hp.application.use_cases.get_hp_operations import GetHpOperations
from src.modules.analisis_log_hp.application.use_cases.get_remote_ews import GetRemoteEws
from src.modules.analisis_log_hp.application.use_cases.get_solution_proxy import (
    GetSolutionProxy,
)
from src.modules.analisis_log_hp.application.use_cases.refresh_hp_cache import RefreshHpCache
from src.modules.analisis_log_hp.application.use_cases.resolve_device import ResolveDevice
from src.modules.analisis_log_hp.application.use_cases.upsert_error_code import UpsertErrorCode
from src.modules.analisis_log_hp.domain.errors import ErrorCodeNotFoundError
from tests.unit.application.analisis_log_hp.fake_gateways import (
    FakeAiGateway,
    FakeHpInsightGateway,
    FakeHpPortalGateway,
)
from tests.unit.application.analisis_log_hp.fakes import (
    FakeCpmdRepo,
    FakeErrorCodeRepo,
    make_error_code,
)


class TestDiagnoseAi:
    def test_costo_suma_los_cuatro_tipos_de_token(self) -> None:
        tokens = {
            "input": 1_000_000, "output": 1_000_000, "cache_write": 1_000_000,
            "cache_read": 1_000_000,
        }
        assert _cost(tokens) == pytest.approx(3.00 + 15.00 + 3.75 + 0.30)

    def test_costo_sin_tokens_es_cero(self) -> None:
        assert _cost({}) == 0.0

    async def test_diagnose_devuelve_texto_tokens_y_costo(self) -> None:
        ai = FakeAiGateway(tokens={"input": 1_000_000})
        result = await DiagnoseAi(ai).execute({"incidents": []}, "claude-x")
        assert result.diagnosis == '{"despacho": "si"}'
        assert result.cost_usd == pytest.approx(3.00)
        assert ai.calls[0][0] == "diagnose"
        assert ai.calls[0][2] == "claude-x"

    async def test_pdf_summary_usa_el_metodo_de_resumen(self) -> None:
        ai = FakeAiGateway(text="resumen", tokens={"output": 1_000_000})
        result = await GeneratePdfSummary(ai).execute({}, "m")
        assert (result.diagnosis, result.cost_usd) == ("resumen", pytest.approx(15.0))
        assert ai.calls[0][0] == "pdf"


class TestCpmd:
    async def test_upload_find_y_get(self) -> None:
        repo = FakeCpmdRepo()
        manual = await UploadCpmdManual(repo).execute(
            keywords=["M404", "M428"], label="LaserJet M4xx", filename="a.pdf"
        )
        assert manual.id == 1
        assert await FindCpmdManual(repo).execute("HP LaserJet m428dw") == manual
        assert await FindCpmdManual(repo).execute("E52645") is None
        assert await GetCpmdManualById(repo).execute(1) == manual
        assert await GetCpmdManualById(repo).execute(99) is None


class TestInsightLiveData:
    async def test_consumibles_alertas_y_metros_delegan_al_gateway(self) -> None:
        gw = FakeHpInsightGateway()
        assert await GetDeviceConsumables(gw).execute(5) == [{"color": "black", "level": 40}]
        assert await GetDeviceAlerts(gw).execute(5) == [{"alert": "current"}]
        assert await GetDeviceAlerts(gw).execute(
            5, current_only=False, from_date="2026-01-01", max_results=3
        ) == [{"alert": "history"}]
        assert await GetDeviceMeters(gw).execute(5, days=30) == [{"meter": 30}]
        assert ("alerts_history", (5, "2026-01-01", None, 3)) in gw.calls

    async def test_dispositivos_de_cliente_se_traducen_al_shape_del_frontend(self) -> None:
        devices = await GetClientDevices(FakeHpInsightGateway()).execute(9)
        assert devices[0] == {"device_id": 1, "serial": "S1", "location": "Z", "model": "M"}
        assert devices[1] == {"device_id": 2, "serial": "", "location": None, "model": None}

    async def test_clientes_usan_name_o_customer_name_y_device_count_cero(self) -> None:
        clients = await GetClients(FakeHpInsightGateway()).execute()
        assert clients == [
            {"customer_id": 1, "name": "Yaguar", "device_count": 0},
            {"customer_id": 2, "name": "Otro", "device_count": 0},
        ]

    async def test_resolve_device_normaliza_el_serial(self) -> None:
        gw = FakeHpInsightGateway(device={"deviceId": 1})
        assert await ResolveDevice(gw).execute(" abc ") == {"deviceId": 1}
        assert gw.calls == [("search_by_serial", "ABC")]


class TestPortalSimples:
    async def test_operaciones_ews_y_refresh_delegan_al_portal(self) -> None:
        portal = FakeHpPortalGateway()
        assert await GetHpOperations(portal).execute("7") == [{"operation": "Op", "sent": "hoy"}]
        assert await GetRemoteEws(portal).execute("7") == "https://ews/7"
        baseline = await RefreshHpCache(portal).execute("7")
        assert baseline[0]["operation"] == "RefreshHPCloudDeviceActionCache"
        assert [c[0] for c in portal.calls] == [
            "get_hp_operations", "fetch_remote_ews_url", "refresh_hp_cache"
        ]


class TestGetSolutionProxy:
    async def test_codigo_inexistente_lanza_not_found(self) -> None:
        with pytest.raises(ErrorCodeNotFoundError):
            await GetSolutionProxy(FakeErrorCodeRepo(), FakeHpPortalGateway()).execute("x")

    async def test_sin_url_devuelve_el_contenido_cacheado(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("A", solution_url=None)])
        portal = FakeHpPortalGateway()
        assert await GetSolutionProxy(repo, portal).execute("A") == "<p>cache</p>"
        assert portal.calls == []

    async def test_con_url_fetchea_en_vivo(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("A")])
        portal = FakeHpPortalGateway(solution_content="<p>vivo</p>")
        assert await GetSolutionProxy(repo, portal).execute("A") == "<p>vivo</p>"
        assert portal.calls == [("fetch_solution_content", "http://sds/13.20")]

    async def test_falla_en_vivo_cae_a_cache(self) -> None:
        repo = FakeErrorCodeRepo([make_error_code("A")])
        portal = FakeHpPortalGateway(solution_error=RuntimeError("timeout"))
        assert await GetSolutionProxy(repo, portal).execute("A") == "<p>cache</p>"


class TestUpsertErrorCode:
    async def test_con_url_fetchea_contenido_y_lo_guarda(self) -> None:
        repo = FakeErrorCodeRepo()
        portal = FakeHpPortalGateway(solution_content="<p>vivo</p>")
        await UpsertErrorCode(repo, portal).execute("A", "ERROR", "desc", "http://u")
        assert repo.upserts == [{
            "code": "A", "severity": "ERROR", "description": "desc",
            "solution_url": "http://u", "solution_content": "<p>vivo</p>",
        }]

    async def test_campos_vacios_se_normalizan_a_none(self) -> None:
        repo = FakeErrorCodeRepo()
        portal = FakeHpPortalGateway()
        await UpsertErrorCode(repo, portal).execute("A", "", "", "")
        assert repo.upserts[0] == {
            "code": "A", "severity": None, "description": None,
            "solution_url": None, "solution_content": None,
        }
        assert portal.calls == []

    async def test_falla_del_fetch_guarda_sin_contenido(self) -> None:
        repo = FakeErrorCodeRepo()
        portal = FakeHpPortalGateway(solution_error=RuntimeError("timeout"))
        result = await UpsertErrorCode(repo, portal).execute("A", None, None, "http://u")
        assert repo.upserts[0]["solution_content"] is None
        assert result.code == "A"
