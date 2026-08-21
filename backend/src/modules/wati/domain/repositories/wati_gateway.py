from typing import Protocol

from src.modules.wati.domain.value_objects.evento import ContactoWati, EventoWati


class WatiGateway(Protocol):
    """Lectura de la API de WATI. Solo lectura: este módulo nunca escribe
    en WATI (no asigna, no cierra, no manda mensajes)."""

    async def list_contactos_recientes(self, limite: int) -> list[ContactoWati]:
        """Contactos ordenados por `last_updated` descendente (así los
        devuelve la API), a lo sumo `limite`."""
        ...

    async def get_eventos(self, wa_id: str, limite: int) -> list[EventoWati]:
        """Últimos `limite` eventos (mensajes + ticket) del chat con ese número."""
        ...
