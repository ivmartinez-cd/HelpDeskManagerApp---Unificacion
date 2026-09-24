"""Caso de uso de lectura "Reclamar en OCA": arma los datos que el operador carga en el
formulario público de reclamos de OCA (contacto de la cuenta, guía y comentario sugerido).
No escribe nada ni habla con OCA: el envío del formulario lo hace el operador."""

from collections.abc import Sequence

from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ObtenerDetalleDespacho,
)
from src.modules.insumos.domain.services.despachados.comentario_reclamo import (
    comentario_reclamo,
)
from src.modules.insumos.domain.value_objects.despachados.reclamo_oca import (
    ReclamoOca,
    ReglaContactoReclamo,
    contacto_para_guia,
)


class PrepararReclamoOca:
    def __init__(
        self, detalle: ObtenerDetalleDespacho, reglas: Sequence[ReglaContactoReclamo]
    ) -> None:
        self._detalle = detalle
        self._reglas = tuple(reglas)

    async def execute(self, guia: str) -> ReclamoOca:
        """`EnvioDespachoNoEncontradoError` (404) si la guía no se sigue."""
        detalle = await self._detalle.execute(guia)
        estado = detalle.envio.estado_oca
        return ReclamoOca(
            guia=guia,
            operativa=estado.operativa if estado else "",
            contacto=contacto_para_guia(guia, self._reglas),
            comentario=comentario_reclamo(detalle.envio, detalle.remitos),
        )
