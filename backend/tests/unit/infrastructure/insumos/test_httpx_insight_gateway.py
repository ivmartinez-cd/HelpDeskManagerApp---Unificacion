"""Tests de HttpxInsightGateway contra httpx.MockTransport (sin red).

Porta los casos de test_insight_client.py del legacy (cache de token, validación de
listas, endpoint de monitors) y agrega los contratos nuevos del adapter: margen de
refresco del token, reintentos SOLO en GET.
"""

import json

import httpx
import pytest

from src.modules.insumos.domain.errors import RespuestaInesperadaDeInsightError
from src.modules.insumos.infrastructure.insight.httpx_insight_gateway import HttpxInsightGateway
from src.shared.domain.errors import ExternalServiceError

_LOGIN_OK = {"access_token": "tok-123", "expires_in": 3600}


class _Recorder:
    def __init__(self, expires_in: int = 3600):
        self.login_count = 0
        self.requests: list[httpx.Request] = []
        self.expires_in = expires_in
        # path -> respuesta (payload JSON o callable(request) -> httpx.Response)
        self.responses: dict[str, object] = {}

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/login"):
            self.login_count += 1
            return httpx.Response(
                200, json={"access_token": "tok-123", "expires_in": self.expires_in}
            )
        self.requests.append(request)
        value = self.responses.get(request.url.path)
        if callable(value):
            response = value(request)
            assert isinstance(response, httpx.Response)
            return response
        if value is None:
            raise AssertionError(f"test no configuró respuesta para {request.url.path}")
        return httpx.Response(200, json=value)


def _gateway(recorder: _Recorder) -> HttpxInsightGateway:
    return HttpxInsightGateway(
        "https://insight.example",
        "k",
        "s",
        transport=httpx.MockTransport(recorder.handler),
    )


async def test_get_list_devuelve_la_lista() -> None:
    recorder = _Recorder()
    recorder.responses["/api/customers"] = [{"id": 1}, {"id": 2}]

    assert await _gateway(recorder).get_customers() == [{"id": 1}, {"id": 2}]


async def test_get_list_rechaza_objeto_suelto() -> None:
    recorder = _Recorder()
    recorder.responses["/api/customers"] = {"error": "algo raro"}

    with pytest.raises(RespuestaInesperadaDeInsightError, match="devolvió un objeto"):
        await _gateway(recorder).get_customers()


async def test_get_monitors_llama_el_endpoint_correcto() -> None:
    recorder = _Recorder()
    recorder.responses["/api/monitors"] = [
        {"name": "cliente-central", "online": False, "status": "ACTIVE"}
    ]

    monitors = await _gateway(recorder).get_monitors(8251)

    request = recorder.requests[0]
    assert request.url.path == "/api/monitors"
    assert request.url.params["customerId"] == "8251"
    assert request.url.params["includeExtendedFields"] == "true"
    assert monitors == [{"name": "cliente-central", "online": False, "status": "ACTIVE"}]


async def test_ensure_token_no_reloguea_si_sigue_vigente() -> None:
    recorder = _Recorder()
    recorder.responses["/api/customers"] = []
    gateway = _gateway(recorder)

    await gateway.get_customers()
    await gateway.get_customers()

    assert recorder.login_count == 1


async def test_token_se_renueva_cuando_entra_en_el_margen_de_refresco() -> None:
    """Con expires_in=300 el token vence "ya" (300s de vida - 300s de margen = 0):
    la segunda llamada debe re-loguear en vez de usar un token por vencer."""
    recorder = _Recorder(expires_in=300)
    recorder.responses["/api/customers"] = []
    gateway = _gateway(recorder)

    await gateway.get_customers()
    await gateway.get_customers()

    assert recorder.login_count == 2


async def test_get_reintenta_ante_503_y_devuelve_el_resultado() -> None:
    recorder = _Recorder()
    attempts = {"n": 0}

    def flaky(_request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            return httpx.Response(503, text="mantenimiento")
        return httpx.Response(200, json=[{"id": 1}])

    recorder.responses["/api/customers"] = flaky

    assert await _gateway(recorder).get_customers() == [{"id": 1}]
    assert attempts["n"] == 2


async def test_patch_no_reintenta_ante_503() -> None:
    """Reintentar una mutación arriesga efectos dobles — misma regla que el legacy
    (Retry con POST/PATCH excluidos a propósito)."""
    recorder = _Recorder()
    attempts = {"n": 0}

    def failing(_request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(503, text="mantenimiento")

    recorder.responses["/api/consumable-requests/9"] = failing

    with pytest.raises(ExternalServiceError, match="503"):
        await _gateway(recorder).update_consumable_request(9, status_update="ACTION")

    assert attempts["n"] == 1


async def test_update_consumable_request_solo_manda_los_campos_presentes() -> None:
    recorder = _Recorder()
    captured: dict[str, object] = {}

    def capture(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"ok": True})

    recorder.responses["/api/consumable-requests/9"] = capture

    await _gateway(recorder).update_consumable_request(
        9, external_ref="441770-3", status_update="ACTION"
    )

    # Nótese ACTION, no ACTIONED (bug corregido documentado en el CHANGELOG legacy).
    assert captured == {"externalRef": "441770-3", "statusUpdate": "ACTION"}


async def test_get_device_by_id_desenvuelve_el_resultado_de_search() -> None:
    recorder = _Recorder()
    recorder.responses["/api/devices/search"] = [{"deviceId": 7, "serialNumber": "SERIE1"}]

    device = await _gateway(recorder).get_device_by_id(7)

    assert device == {"deviceId": 7, "serialNumber": "SERIE1"}
    assert recorder.requests[0].url.params["q"] == "deviceId:7"


async def test_get_device_consumables_desenvuelve_la_lista() -> None:
    recorder = _Recorder()
    recorder.responses["/api/devices/7/consumables"] = {"consumables": [{"index": 0}]}

    assert await _gateway(recorder).get_device_consumables(7) == [{"index": 0}]


async def test_get_consumable_history_desenvuelve_history_steps() -> None:
    recorder = _Recorder()
    recorder.responses["/api/devices/7/consumables/history"] = {
        "historySteps": [{"recordDate": "2026-08-01T10:00:00Z"}]
    }

    steps = await _gateway(recorder).get_consumable_history(7, 0, start_date="2026-08-01T00:00:00Z")

    assert steps == [{"recordDate": "2026-08-01T10:00:00Z"}]
    assert recorder.requests[0].url.params["consumableIndex"] == "0"
    assert recorder.requests[0].url.params["startDate"] == "2026-08-01T00:00:00Z"
