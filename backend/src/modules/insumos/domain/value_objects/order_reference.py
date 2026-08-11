"""Clave de idempotencia de pedidos: NroIncidenteCliente = "SDS-{hp_request_id}".

Es el campo que Canal Directo devuelve intacto en getSupplyById y que la verificación
post-creación compara con igualdad exacta. No se persiste como columna propia — se
reconstruye al vuelo desde `hp_request_id` (PK de processed_requests), igual que en el
legacy (poller.create_order_and_record).
"""

REFERENCE_PREFIX = "SDS-"

# Pedidos previos a jul-2026 usan "HP-" (CHANGELOG legacy [1.1.0]) — es un detalle de
# formato del lado de Canal Directo, sin migración retroactiva: no hay de dónde derivarlo
# si se pierde.
LEGACY_REFERENCE_PREFIX = "HP-"


def order_reference(hp_request_id: int) -> str:
    return f"{REFERENCE_PREFIX}{hp_request_id}"
