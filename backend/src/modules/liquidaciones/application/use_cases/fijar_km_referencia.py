"""FijarKmReferencia — toma como km de referencia de una sucursal lo que el
prestador cobró, con la TL confirmando desde la alerta ALT002 "sin km de
referencia". Así la Tabla KM se completa sola a medida que las liquidaciones
pasan, en vez de cargar 1.660 filas a mano (60 % de la tabla estaba sin km al
2026-09-05; solo 75 de esas filas se usaron en 2026). Misma búsqueda por clave
normalizada que `AsignarZonaSucursal`; el reanálisis lo dispara el router."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import (
    KmReferenciaInvalidoError,
    ParSinTablaKmError,
    TablaKmNoEncontradaError,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    clave_empresa_sucursal,
)


@dataclass(frozen=True)
class FijarKmReferenciaPorts:
    tabla_km: TablaKmRepository


class FijarKmReferencia:
    def __init__(self, ports: FijarKmReferenciaPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID, *, empresa_nombre: str, sucursal_nombre: str, kms: float
    ) -> TablaKm:
        if kms <= 0:
            raise KmReferenciaInvalidoError("Los km de referencia tienen que ser mayores a 0")
        fila = await self._buscar_fila(prestador_id, empresa_nombre, sucursal_nombre)
        actualizada = await self._ports.tabla_km.update_kms_a_facturar(fila.id, kms)
        if actualizada is None:
            raise TablaKmNoEncontradaError(fila.id)
        return actualizada

    async def _buscar_fila(self, prestador_id: UUID, empresa: str, sucursal: str) -> TablaKm:
        clave = clave_empresa_sucursal(empresa, sucursal)
        for fila in await self._ports.tabla_km.list_by_prestador(prestador_id):
            if clave_empresa_sucursal(fila.empresa_nombre, fila.sucursal_nombre) == clave:
                return fila
        raise ParSinTablaKmError(empresa, sucursal)
