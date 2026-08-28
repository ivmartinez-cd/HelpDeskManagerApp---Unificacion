"""Puerto del aviso por mail al cliente cuando se carga su pedido (ver
domain/value_objects/client_order_notice.py). Implementación en infrastructure: SMTP
dedicado (CLIENT_MAIL_SMTP_*), separado del mailer interno — remitente/relay propios
para destinatarios externos."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.client_order_notice import ClientOrderNotice


class ClientOrderNotifier(Protocol):
    async def notify(self, notice: ClientOrderNotice) -> None:
        """Arma y envía el mail; deja rastro en mail_log (éxito o falla) y propaga la
        excepción si el envío falla — el caller decide si contenerla."""
        ...
