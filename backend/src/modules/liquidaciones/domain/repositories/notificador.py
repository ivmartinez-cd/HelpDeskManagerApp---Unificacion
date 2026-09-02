"""Puerto de notificaciones de liquidaciones — mail de aviso a jpcorigliano@
canaldirecto.com.ar al aprobar (paridad literal con Web Agentes/CakePHP legacy
para este mismo evento). Sin cadena de aprobación de dos pasos todavía
(jpcorigliano→gerente queda pendiente, decisión consciente del usuario)."""

from typing import Protocol

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


class Notificador(Protocol):
    async def notificar_aprobacion(self, liquidacion: Liquidacion) -> None:
        """Nunca debe propagar: un fallo de envío no puede romper la aprobación,
        que ya está confirmada en wsAyC y localmente cuando esto se invoca."""
        ...
