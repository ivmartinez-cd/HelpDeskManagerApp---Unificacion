"""Impl del puerto Notificador — mail de aviso de aprobación a jpcorigliano@
canaldirecto.com.ar, mismo asunto/cuerpo literal que usa el legacy Web Agentes
(CakePHP) para este evento. Un fallo de envío nunca corta la aprobación —ya
confirmada en wsAyC y local cuando esto se invoca—: se loguea acá y se sigue,
mismo criterio que `vacaciones/infrastructure/email_notificador.py`."""

import logging

from src.modules.auth.domain.services.mailer import Mailer
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion

_logger = logging.getLogger(__name__)

_DESTINATARIO_APROBACION = "jpcorigliano@canaldirecto.com.ar"


class EmailNotificador:
    def __init__(self, mailer: Mailer, frontend_url: str) -> None:
        self._mailer = mailer
        self._frontend_url = frontend_url.rstrip("/")

    async def notificar_aprobacion(self, liquidacion: Liquidacion) -> None:
        codigo = liquidacion.numero_liquidacion
        subject, body, html_body = self._construir_mensaje(liquidacion)
        try:
            await self._mailer.send(
                to=_DESTINATARIO_APROBACION, subject=subject, body=body, html_body=html_body
            )
        except Exception as exc:
            _logger.error(
                "email_notificador: falló el aviso de aprobación de liquidación",
                extra={"liquidacion_id": str(liquidacion.id), "numero": codigo},
                exc_info=exc,
            )

    def _construir_mensaje(self, liquidacion: Liquidacion) -> tuple[str, str, str]:
        codigo = liquidacion.numero_liquidacion
        url = f"{self._frontend_url}/liquidaciones/{liquidacion.id}"
        subject = f"Aviso CanalDirecto - Se APROBO la Liquidacion nro: {codigo}"
        html_body = (
            f"Les informamos que se ha aprobado la Liquidacion nro: {codigo}<br />\n"
            "Para ver los detalles de la misma haga clic en el siguiente vinculo: "
            f'<a href="{url}">Ver</a><br />\n'
            "<br />\n"
            "CANAL DIRECTO"
        )
        body = (
            f"Les informamos que se ha aprobado la Liquidacion nro: {codigo}\n"
            f"Para ver los detalles de la misma ingresá a: {url}\n\n"
            "CANAL DIRECTO"
        )
        return subject, body, html_body
