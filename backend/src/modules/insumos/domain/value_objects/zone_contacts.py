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


@dataclass(frozen=True)
class ZoneContactRow:
    """Fila completa de customer_zone_contacts para vistas de listado y edición."""

    zone: str
    sol_apellido: str = ""
    sol_nombre: str = ""
    sol_telefono: str = ""
    sol_email: str = ""
    sol_sector: str = ""
    dest_apellido: str = ""
    dest_nombre: str = ""
    dest_telefono: str = ""
    dest_email: str = ""
    dest_sector: str = ""
    observaciones: str = ""


@dataclass(frozen=True)
class ZoneContactPreviewRow:
    """Vista previa de importación desde el PortalWeb de SDS (sin escribir)."""

    zone: str
    apellido: str = ""
    nombre: str = ""
    email: str = ""
    telefono: str = ""
    already_configured: bool = False
    error: str | None = None
    current_apellido: str = ""
    current_nombre: str = ""
    current_email: str = ""
    current_telefono: str = ""


@dataclass(frozen=True)
class ZoneOverwriteRequest:
    zone: str
    overwrite: bool = False


@dataclass(frozen=True)
class Customer:
    """Cliente sincronizado desde Insight."""

    customer_id: int
    name: str
    enabled: bool
    has_contacts: bool = False
    # Opt-in de aviso por mail al cliente al cargar su pedido (ver
    # domain/value_objects/client_order_notice.py) — apagado por default en toda la
    # cartera.
    client_mail_enabled: bool = False


@dataclass(frozen=True)
class SdsContactRow:
    """Contacto detectado en el comentario de un equipo de SDS Insight."""

    zone: str
    contacto: str
    email: str
    sucursal: str
