"""Fase de ListRequests: aviso de entrega alternativa por zona (ver
domain/services/zone_delivery_notice.py). Se resuelve UNA VEZ por (customer_id, store),
no por fila, reusando list_all(customer_id) — un solo SELECT por cliente en vez de
repetir la misma lectura de zona en cada solicitud del mismo cliente/zona."""

from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.domain.repositories.zone_contact_repository import (
    ZoneContactRepository,
)
from src.modules.insumos.domain.services.zone_delivery_notice import (
    SucursalOverride,
    detect_sucursal_override,
)
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContactRow


async def attach_zone_delivery_notices(
    rows: list[RequestRow], zone_contacts: ZoneContactRepository
) -> None:
    """Replica la misma cadena de fallback que load_order._resolve_zone_contacts: la
    zona específica solo cuenta si tiene solicitante con nombre propio; si no, cae a la
    zona default (''). Sin eso, el aviso podría mostrar la observación de una zona que
    load_order en realidad no va a usar al cargar el pedido."""
    zones_by_customer: dict[int, dict[str, ZoneContactRow]] = {}
    overrides_by_key: dict[tuple[int, str], SucursalOverride] = {}

    for row in rows:
        if row.customer_id is None:
            continue
        key = (row.customer_id, row.store)
        override = overrides_by_key.get(key)
        if override is None:
            zones = zones_by_customer.get(row.customer_id)
            if zones is None:
                zones = {z.zone: z for z in await zone_contacts.list_all(row.customer_id)}
                zones_by_customer[row.customer_id] = zones
            override = detect_sucursal_override(_observaciones_for(zones, row.store))
            overrides_by_key[key] = override
        row.requiere_cambio_sucursal = override.requiere_cambio
        row.sucursal_entrega = override.sucursal
        row.observacion_zona = override.observacion or None


def _observaciones_for(zones: dict[str, ZoneContactRow], store: str) -> str:
    specific = zones.get(store)
    if specific is not None and (specific.sol_apellido.strip() or specific.sol_nombre.strip()):
        return specific.observaciones
    default = zones.get("")
    return default.observaciones if default is not None else ""
