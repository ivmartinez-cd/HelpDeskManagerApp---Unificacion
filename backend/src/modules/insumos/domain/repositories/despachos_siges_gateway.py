"""Puerto de lectura de los remitos de insumos despachados por OCA en SiGes.

Solo lectura: la cuenta `SiGesReadOnly` de ORION no tiene permisos de escritura.
"""

from typing import Protocol

from src.modules.insumos.domain.value_objects.despachados.despacho_siges import DespachoSiges


class DespachosSigesGateway(Protocol):
    async def listar_despachos_oca(
        self, *, dias_ventana: int, distribuciones: tuple[int, ...]
    ) -> list[DespachoSiges]:
        """Remitos de insumos (`TipoRemito='I'`) con guía OCA de 19 dígitos, de los
        transportes `distribuciones`, con `Fecha_Remito` en los últimos `dias_ventana`
        días. Uno por remito, con sus incidentes agrupados."""
        ...
