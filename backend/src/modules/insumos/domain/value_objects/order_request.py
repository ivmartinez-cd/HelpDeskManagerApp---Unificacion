"""El pedido de insumos a crear en Canal Directo — portado de canal_directo_client.py."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    sku: str
    quantity: int
    description: str = ""  # descripción libre del consumible (ej. "Cartucho amarillo HP 414A")


@dataclass(frozen=True)
class ContactInfo:
    apellido: str = ""
    nombre: str = ""
    telefono: str = ""
    email: str = ""
    sector: str = ""


@dataclass(frozen=True)
class OrderRequest:
    customer_id: int
    customer_name: str
    store_name: str
    device_serial: str
    lines: tuple[OrderLine, ...]
    reference: str  # clave de idempotencia propia, ej. order_reference(hp_request_id)
    # Si se proporcionan, reemplazan los datos globales de la config para este pedido.
    solicitante: ContactInfo | None = None
    destinatario: ContactInfo | None = None
    detalle: str | None = None
    # Cuando el operador desambiguó manualmente un insumo (ver InsumoAmbiguoError), el
    # frontend reenvía su elección acá para saltear la búsqueda automática de insumo_matching.
    override_insumo_id: str | None = None
    revision: bool = True
