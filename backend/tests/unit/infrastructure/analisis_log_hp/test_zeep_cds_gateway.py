"""ZeepCdsGateway con un provider falso: mapea cada operación SOAP a su parser
y degrada a lista vacía cuando SOAP falla (salvo getMachineBySerial)."""

import json
from typing import Any

import pytest

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsReplacement
from src.modules.analisis_log_hp.infrastructure.wsayc.zeep_cds_gateway import ZeepCdsGateway


class _Service:
    def __init__(self, responses: dict[str, Any], *, fail: bool = False) -> None:
        self._responses = responses
        self._fail = fail
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __getattr__(self, name: str) -> Any:
        def op(**kwargs: Any) -> Any:
            self.calls.append((name, kwargs))
            if self._fail:
                raise RuntimeError("SOAP caído")
            return self._responses.get(name)

        return op


class _Provider:
    def __init__(self, service: _Service) -> None:
        self._svc = service

    def service(self) -> _Service:
        return self._svc


def _gateway(responses: dict[str, Any] | None = None, *, fail: bool = False) -> ZeepCdsGateway:
    svc = _Service(responses or {}, fail=fail)
    gw = ZeepCdsGateway(provider=_Provider(svc))  # type: ignore[arg-type]
    gw.svc = svc  # type: ignore[attr-defined]
    return gw


async def test_get_machine_by_serial_parsea_y_pasa_el_serial() -> None:
    gw = _gateway({"getMachineBySerial": json.dumps({"Machine": {"id": 1, "empresa_id": 2}})})
    assert await gw.get_machine_by_serial("ABC") == ("1", "2")
    assert gw.svc.calls == [("getMachineBySerial", {"SerialNumber": "ABC"})]  # type: ignore[attr-defined]


async def test_get_machine_by_serial_propaga_errores_soap() -> None:
    with pytest.raises(RuntimeError):
        await _gateway(fail=True).get_machine_by_serial("ABC")


async def test_get_machine_incidents_usa_parametros_del_legacy() -> None:
    gw = _gateway({"getMachineIncidents": json.dumps([{"Incident": {"id": "9"}}])})
    assert await gw.get_machine_incidents("M1", "") == [{"id": "9"}]
    _, kwargs = gw.svc.calls[0]  # type: ignore[attr-defined]
    assert kwargs == {
        "IdMaquina": "M1", "IdEmpresa": "", "IdSucursal": "", "IdSector": "",
        "top": "50", "estado": "", "tipo": "Todos",
    }


async def test_get_counters_replacements_y_jobs_mapean_a_sus_parsers() -> None:
    gw = _gateway({
        "getCounters": json.dumps([{"Counter": {"Contador": "5"}}]),
        "getIncidentReplacements": json.dumps([{"Replacement": {"Articulo": "Fusor"}}]),
        "getIncidentJobs": json.dumps([{"Job": {"Descripcion": "Cambio"}}]),
    })
    assert await gw.get_counters("M1") == [{"Contador": "5"}]
    assert await gw.get_incident_replacements("I1") == [CdsReplacement("Fusor", 1)]
    assert await gw.get_incident_jobs("I1") == ["Cambio"]
    nombres = [c[0] for c in gw.svc.calls]  # type: ignore[attr-defined]
    assert nombres == ["getCounters", "getIncidentReplacements", "getIncidentJobs"]


async def test_fallas_soap_en_consultas_secundarias_devuelven_vacio() -> None:
    gw = _gateway(fail=True)
    assert await gw.get_machine_incidents("M1", "E1") == []
    assert await gw.get_counters("M1") == []
    assert await gw.get_incident_replacements("I1") == []
    assert await gw.get_incident_jobs("I1") == []
