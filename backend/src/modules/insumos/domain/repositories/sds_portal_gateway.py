"""Puerto para la baja de equipos en el PortalWeb de SDS Insight (scraping)."""

from typing import Protocol


class SdsPortalGateway(Protocol):
    async def delete_device(self, device_id: int) -> None:
        """Da de baja el equipo en el PortalWeb de SDS.

        Nunca reintenta el POST de baja (operación irreversible, un retry duplicaría
        la baja). El único reintento permitido es el re-login previo al POST, y solo
        ante la señal confirmada de sesión vencida (redirect a /login). Ver ADR-008
        y el comentario del incidente 2026-07-30 en httpx_sds_portal_gateway.py.

        Lanza ExternalServiceError si el portal no confirma la baja.
        """
        ...
