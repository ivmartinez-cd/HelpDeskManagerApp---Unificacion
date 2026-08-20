"""Tests de CanalDirectoIncidentCreation (kit de mantenimiento → persistNewIncident)."""

import pytest

from src.modules.insumos.domain.errors import (
    IncidenteNoConfirmadoError,
    IncidenteNoVerificadoError,
)
from src.modules.insumos.domain.services.incident_creation import CanalDirectoIncidentCreation
from src.modules.insumos.domain.value_objects.cd_supply import CdSupply
from src.modules.insumos.domain.value_objects.incident_request import IncidentRequest
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from tests.unit.domain.insumos.fakes import FakeWsAycGateway, settings

_NO_WAIT = (0,)


def _incident(**overrides: object) -> IncidentRequest:
    base: dict[str, object] = {
        "device_serial": "SERIE1",
        "reference": "SDS-123",
        "falla": "Kit de mantenimiento solicitado por SDS: Fuser kit HP",
        "origen_id": "",
    }
    base.update(overrides)
    return IncidentRequest(**base)  # type: ignore[arg-type]


def _service(
    gateway: FakeWsAycGateway, delays: tuple[float, ...] = _NO_WAIT
) -> CanalDirectoIncidentCreation:
    return CanalDirectoIncidentCreation(gateway, settings(), verify_delays=delays)


async def test_create_incident_ok_devuelve_id_sin_check_digit() -> None:
    gateway = FakeWsAycGateway()
    gateway.incidents_by_id[gateway.persist_incident_result] = CdSupply(
        supply_id=gateway.persist_incident_result, reference="SDS-123"
    )
    service = _service(gateway)

    incident_id = await service.create_incident(_incident())

    assert incident_id == str(gateway.persist_incident_result)
    payload = gateway.persisted_incident_payloads[0]["Incident"]
    assert payload["NroSerie"] == "SERIE1"
    assert payload["NroIncidenteCliente"] == "SDS-123"
    assert payload["Ingreso"] != "guardia" and payload["Ingreso"]
    assert payload["origen_id"] == "6"  # cae al default de settings (origen_id="")


async def test_create_incident_usa_origen_id_propio_si_viene() -> None:
    gateway = FakeWsAycGateway()
    gateway.incidents_by_id[gateway.persist_incident_result] = CdSupply(
        supply_id=gateway.persist_incident_result, reference="SDS-123"
    )
    service = _service(gateway)

    await service.create_incident(_incident(origen_id="5"))

    assert gateway.persisted_incident_payloads[0]["Incident"]["origen_id"] == "5"


async def test_create_incident_usa_contacto_propio_si_viene() -> None:
    gateway = FakeWsAycGateway()
    gateway.incidents_by_id[gateway.persist_incident_result] = CdSupply(
        supply_id=gateway.persist_incident_result, reference="SDS-123"
    )
    service = _service(gateway)
    zona = ContactInfo(apellido="Diaz", nombre="Marta", telefono="1199998888", email="m@e.com")

    await service.create_incident(_incident(solicitante=zona))

    sol = gateway.persisted_incident_payloads[0]["Incident"]
    assert sol["ApellidoSolicitante"] == "Diaz"
    assert sol["NombreSolicitante"] == "Marta"


async def test_no_confirmado_lanza_error_de_dominio() -> None:
    gateway = FakeWsAycGateway()
    gateway.persist_incident_result = 0
    service = _service(gateway)

    with pytest.raises(IncidenteNoConfirmadoError):
        await service.create_incident(_incident())


async def test_no_verificado_lanza_error_de_dominio() -> None:
    """La relectura no encuentra el ID (o la referencia no coincide) — nunca se debe
    dar por creado sin confirmar, mismo criterio que PedidoNoVerificadoError."""
    gateway = FakeWsAycGateway()  # incidents_by_id vacío a propósito
    service = _service(gateway)

    with pytest.raises(IncidenteNoVerificadoError):
        await service.create_incident(_incident())


async def test_referencia_no_coincide_no_verifica() -> None:
    gateway = FakeWsAycGateway()
    gateway.incidents_by_id[gateway.persist_incident_result] = CdSupply(
        supply_id=gateway.persist_incident_result, reference="SDS-OTRA-COSA"
    )
    service = _service(gateway)

    with pytest.raises(IncidenteNoVerificadoError):
        await service.create_incident(_incident())
