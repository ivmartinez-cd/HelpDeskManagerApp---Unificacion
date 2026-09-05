"""Puerto del catálogo de acuerdos de precio por cliente (ver la entidad)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.acuerdo_precio_cliente import (
    AcuerdoPrecioCliente,
)
from src.modules.liquidaciones.domain.value_objects.acuerdo_precio_datos import (
    AcuerdoPrecioDatos,
)


class AcuerdoPrecioClienteRepository(Protocol):
    async def get_by_id(self, acuerdo_id: UUID) -> AcuerdoPrecioCliente | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[AcuerdoPrecioCliente]: ...

    async def create(
        self, prestador_id: UUID, datos: AcuerdoPrecioDatos
    ) -> AcuerdoPrecioCliente: ...

    async def update(
        self, acuerdo_id: UUID, datos: AcuerdoPrecioDatos
    ) -> AcuerdoPrecioCliente | None: ...

    async def delete(self, acuerdo_id: UUID) -> bool: ...
