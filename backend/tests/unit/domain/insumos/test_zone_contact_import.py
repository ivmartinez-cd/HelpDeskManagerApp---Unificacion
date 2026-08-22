"""Tests de preview_zone_contacts — vista previa de contactos por zona desde el PortalWeb."""

from src.modules.insumos.domain.services.zone_contact_import import (
    contact_to_zone_row,
    preview_zone_contacts,
)
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContactRow

_CUSTOMER = 8


def _device(zone_id: int | None, zone: str | None) -> dict:
    return {"extendedFields": {"zoneId": zone_id, "zone": zone}}


class FakeInsight:
    def __init__(self, devices: list[dict], zones: list[dict]) -> None:
        self.devices = devices
        self.zones = zones

    async def get_devices(self, customer_id: int) -> list[dict]:
        return self.devices

    async def get_zones(self, customer_id: int) -> list[dict]:
        return self.zones


class FakePortal:
    def __init__(self) -> None:
        self.contacts: dict[int, ContactInfo | None] = {}
        self.errors: dict[int, Exception] = {}
        self.logins = 0
        self.lookups: list[tuple[int, int]] = []

    async def ensure_login(self) -> None:
        self.logins += 1

    async def get_delivery_location_contact(
        self, customer_id: int, location_id: int
    ) -> ContactInfo | None:
        self.lookups.append((customer_id, location_id))
        if location_id in self.errors:
            raise self.errors[location_id]
        return self.contacts.get(location_id)


async def test_sin_zonas_en_los_equipos_devuelve_vacio_sin_tocar_el_portal() -> None:
    insight = FakeInsight([_device(None, "Norte"), _device(3, ""), {}], [])
    portal = FakePortal()

    rows = await preview_zone_contacts(_CUSTOMER, insight, portal, {})

    assert rows == []
    assert portal.logins == 0


async def test_contacto_nuevo_y_ya_configurado_ordenados_por_zona() -> None:
    insight = FakeInsight(
        [_device(1, "Sur"), _device(1, "SUR"), _device(2, "Norte")],
        [
            {"zoneId": 1, "deliveryLocationId": 10},
            {"zoneId": 2, "deliveryLocationId": 20},
        ],
    )
    portal = FakePortal()
    portal.contacts[10] = ContactInfo(apellido="Pérez Ana", telefono="123", email="a@x")
    portal.contacts[20] = ContactInfo(apellido="Gómez Luis")
    existing = {"Norte": ZoneContactRow(zone="Norte", dest_apellido="Viejo", dest_email="v@x")}

    rows = await preview_zone_contacts(_CUSTOMER, insight, portal, existing)

    assert [r.zone for r in rows] == ["Norte", "SUR", "Sur"]
    assert portal.logins == 1
    assert sorted(portal.lookups) == [(_CUSTOMER, 10), (_CUSTOMER, 20)]
    norte, sur_upper, sur = rows
    assert norte.apellido == "Gómez Luis"
    assert norte.already_configured is True
    assert (norte.current_apellido, norte.current_email) == ("Viejo", "v@x")
    assert sur.apellido == "Pérez Ana"
    assert (sur.telefono, sur.email) == ("123", "a@x")
    assert sur.already_configured is False
    assert sur.current_apellido == ""
    # Las dos variantes de la misma zoneId comparten el contacto scrapeado.
    assert sur_upper.apellido == sur.apellido


async def test_zona_sin_delivery_location_informa_error_por_cada_variante() -> None:
    insight = FakeInsight(
        [_device(1, "Sur"), _device(1, "sur")],
        [{"zoneId": 1, "deliveryLocationId": None}],
    )
    portal = FakePortal()

    rows = await preview_zone_contacts(_CUSTOMER, insight, portal, {})

    assert [(r.zone, r.error) for r in rows] == [
        ("Sur", "Sin ubicación de entrega vinculada en Insight"),
        ("sur", "Sin ubicación de entrega vinculada en Insight"),
    ]
    assert portal.lookups == []


async def test_zona_desconocida_para_insight_informa_error() -> None:
    insight = FakeInsight([_device(7, "Oeste")], [])
    portal = FakePortal()

    rows = await preview_zone_contacts(_CUSTOMER, insight, portal, {})

    assert [(r.zone, r.error) for r in rows] == [
        ("Oeste", "Sin ubicación de entrega vinculada en Insight")
    ]


async def test_error_del_portal_se_informa_en_la_fila_y_no_aborta_el_resto() -> None:
    insight = FakeInsight(
        [_device(1, "Sur"), _device(2, "Norte")],
        [
            {"zoneId": 1, "deliveryLocationId": 10},
            {"zoneId": 2, "deliveryLocationId": 20},
        ],
    )
    portal = FakePortal()
    portal.errors[10] = RuntimeError("portal caído")
    portal.contacts[20] = ContactInfo(apellido="Gómez Luis")

    rows = await preview_zone_contacts(_CUSTOMER, insight, portal, {})

    assert [(r.zone, r.error, r.apellido) for r in rows] == [
        ("Norte", None, "Gómez Luis"),
        ("Sur", "portal caído", ""),
    ]


async def test_delivery_location_sin_contacto_no_genera_filas() -> None:
    insight = FakeInsight([_device(1, "Sur")], [{"zoneId": 1, "deliveryLocationId": 10}])
    portal = FakePortal()
    portal.contacts[10] = None

    rows = await preview_zone_contacts(_CUSTOMER, insight, portal, {})

    assert rows == []


def test_contact_to_zone_row_duplica_solicitante_como_destinatario() -> None:
    row = contact_to_zone_row(
        "Sur", ContactInfo(apellido="Pérez Ana", telefono="123", email="a@x"), "Oficina"
    )

    assert row.zone == "Sur"
    assert (row.sol_apellido, row.dest_apellido) == ("Pérez Ana", "Pérez Ana")
    assert (row.sol_email, row.dest_email) == ("a@x", "a@x")
    assert (row.sol_telefono, row.dest_telefono) == ("123", "123")
    assert row.observaciones == "Oficina"
