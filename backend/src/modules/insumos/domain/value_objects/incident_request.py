"""El incidente Pre-Correctivo (kit de mantenimiento) a crear en Canal Directo.

Más chico que OrderRequest (sin lines/revision/override_insumo_id): un incidente no
elige insumo ni familia, solo asocia una serie a un motivo de visita técnica."""

from dataclasses import dataclass

from src.modules.insumos.domain.value_objects.order_request import ContactInfo


@dataclass(frozen=True)
class IncidentRequest:
    device_serial: str
    reference: str  # clave de idempotencia propia, ej. order_reference(hp_request_id)
    falla: str  # motivo de la visita, con la descripción del kit para el técnico
    origen_id: str
    solicitante: ContactInfo | None = None
    destinatario: ContactInfo | None = None
