"""AsignarZonaSucursal — fija la zona (SPST, o Genérica con `spst_id=None`) de la
fila de Tabla KM de un par empresa+sucursal, desde la alerta ALT008 del detalle
de la liquidación.

Es el reemplazo de "ir a Tabla KM, buscar la sucursal, editar la fila, volver,
Reanalizar" (caso INFOMAC 2026-09-04): la TL decide la zona en el mismo lugar
donde ve el incidente sin precio, y como todos los incidentes de esa sucursal
comparten la fila, se resuelven juntos. El reanálisis lo dispara el router
(`config_routers/_reanalisis.py`). La fila se busca por la misma clave
normalizada que usa el motor (`clave_empresa_sucursal`), así lo que se asigna
acá es exactamente lo que el motor va a resolver."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import (
    ParSinTablaKmError,
    SpstNoEncontradoError,
    TablaKmNoEncontradaError,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    clave_empresa_sucursal,
)


@dataclass(frozen=True)
class AsignarZonaSucursalPorts:
    tabla_km: TablaKmRepository
    spsts: SpstRepository


class AsignarZonaSucursal:
    def __init__(self, ports: AsignarZonaSucursalPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        prestador_id: UUID,
        *,
        empresa_nombre: str,
        sucursal_nombre: str,
        spst_id: UUID | None,
    ) -> TablaKm:
        if spst_id is not None:
            await self._validar_spst(prestador_id, spst_id)
        fila = await self._buscar_fila(prestador_id, empresa_nombre, sucursal_nombre)
        actualizada = await self._ports.tabla_km.update_vinculo_spst(fila.id, spst_id=spst_id)
        if actualizada is None:
            raise TablaKmNoEncontradaError(fila.id)
        return actualizada

    async def _validar_spst(self, prestador_id: UUID, spst_id: UUID) -> None:
        spst = await self._ports.spsts.get_by_id(spst_id)
        if spst is None or spst.prestador_id != prestador_id:
            raise SpstNoEncontradoError(spst_id)

    async def _buscar_fila(self, prestador_id: UUID, empresa: str, sucursal: str) -> TablaKm:
        clave = clave_empresa_sucursal(empresa, sucursal)
        filas = await self._ports.tabla_km.list_by_prestador(prestador_id)
        for fila in filas:
            if clave_empresa_sucursal(fila.empresa_nombre, fila.sucursal_nombre) == clave:
                return fila
        raise ParSinTablaKmError(empresa, sucursal)
