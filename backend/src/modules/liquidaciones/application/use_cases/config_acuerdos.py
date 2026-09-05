"""ABM de acuerdos de precio por cliente (Configuración > Acuerdos). Toda
escritura pasa por acá (validación de "exactamente uno de factor/precio fijo",
motivo obligatorio); el reanálisis de las liquidaciones abiertas lo dispara el
router (`config_routers/_reanalisis.py`), como con tarifarios y Tabla KM."""

from dataclasses import dataclass, replace
from uuid import UUID

from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)
from src.modules.liquidaciones.domain.errors import (
    AcuerdoPrecioInvalidoError,
    AcuerdoPrecioNoEncontradoError,
)
from src.modules.liquidaciones.domain.repositories.acuerdo_precio_cliente_repository import (
    AcuerdoPrecioClienteRepository,
)
from src.modules.liquidaciones.domain.value_objects.acuerdo_precio_datos import (
    AcuerdoPrecioDatos,
)


@dataclass(frozen=True)
class ConfigAcuerdosPorts:
    acuerdos: AcuerdoPrecioClienteRepository


# Alias: los datos editables son el VO de dominio que también usa el puerto.
AcuerdoDatos = AcuerdoPrecioDatos


def validar(datos: AcuerdoDatos) -> AcuerdoDatos:
    if not datos.empresa_nombre.strip():
        raise AcuerdoPrecioInvalidoError("El cliente es obligatorio")
    if not datos.motivo.strip():
        raise AcuerdoPrecioInvalidoError("El motivo es obligatorio")
    if (datos.factor is None) == (datos.precio_fijo is None):
        raise AcuerdoPrecioInvalidoError("Cargá un factor o un precio fijo, no ambos")
    if datos.factor is not None and datos.factor <= 0:
        raise AcuerdoPrecioInvalidoError("El factor tiene que ser mayor a 0")
    if datos.precio_fijo is not None and datos.precio_fijo < 0:
        raise AcuerdoPrecioInvalidoError("El precio fijo no puede ser negativo")
    if datos.vigencia_hasta is not None and datos.vigencia_hasta < datos.vigencia_desde:
        raise AcuerdoPrecioInvalidoError("La vigencia hasta no puede ser anterior a la desde")
    return replace(datos, empresa_nombre=datos.empresa_nombre.strip(), motivo=datos.motivo.strip())


class ListAcuerdos:
    def __init__(self, ports: ConfigAcuerdosPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[AcuerdoPrecioCliente]:
        return await self._ports.acuerdos.list_by_prestador(prestador_id)


class CreateAcuerdo:
    def __init__(self, ports: ConfigAcuerdosPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID, datos: AcuerdoDatos) -> AcuerdoPrecioCliente:
        return await self._ports.acuerdos.create(prestador_id, validar(datos))


class UpdateAcuerdo:
    def __init__(self, ports: ConfigAcuerdosPorts) -> None:
        self._ports = ports

    async def execute(self, acuerdo_id: UUID, datos: AcuerdoDatos) -> AcuerdoPrecioCliente:
        actualizado = await self._ports.acuerdos.update(acuerdo_id, validar(datos))
        if actualizado is None:
            raise AcuerdoPrecioNoEncontradoError(acuerdo_id)
        return actualizado


class DeleteAcuerdo:
    def __init__(self, ports: ConfigAcuerdosPorts) -> None:
        self._ports = ports

    async def execute(self, acuerdo_id: UUID) -> AcuerdoPrecioCliente:
        """Devuelve el acuerdo borrado — el router necesita su `prestador_id`
        para reanalizar las liquidaciones abiertas afectadas."""
        anterior = await self._ports.acuerdos.get_by_id(acuerdo_id)
        if anterior is None or not await self._ports.acuerdos.delete(acuerdo_id):
            raise AcuerdoPrecioNoEncontradoError(acuerdo_id)
        return anterior
