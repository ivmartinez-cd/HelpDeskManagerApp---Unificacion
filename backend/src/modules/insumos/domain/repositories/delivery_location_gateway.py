"""Puerto del PortalWeb de SDS para obtener el contacto de una delivery location."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.order_request import ContactInfo


class DeliveryLocationGateway(Protocol):
    async def ensure_login(self) -> None:
        """Pre-calienta la sesión antes de lookups en paralelo."""
        ...

    async def get_delivery_location_contact(
        self, customer_id: int, location_id: int
    ) -> ContactInfo | None:
        """Contacto cargado en la delivery location, o None si no tiene ninguno.

        Lanza ExternalServiceError si la location no existe o el portal falla."""
        ...
