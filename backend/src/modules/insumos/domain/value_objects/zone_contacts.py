"""Contactos por zona de un cliente (customer_zone_contacts). `zone=""` es la zona
default real — nunca NULL. `observaciones` (ej. "entregar en Oficina Salta") va
primero en el detalle del pedido, antes del texto autogenerado del consumible."""

from dataclasses import dataclass

from src.modules.insumos.domain.value_objects.order_request import ContactInfo


@dataclass(frozen=True)
class ZoneContacts:
    solicitante: ContactInfo
    destinatario: ContactInfo
    observaciones: str = ""

    def has_named_solicitante(self) -> bool:
        """Un registro con solicitante sin nombre ni apellido es inútil para el pedido:
        el caller debe caer a la zona default en vez de usarlo (regla del legacy)."""
        return bool(self.solicitante.apellido.strip() or self.solicitante.nombre.strip())
