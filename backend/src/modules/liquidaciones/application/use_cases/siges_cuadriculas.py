"""Gestión del mapeo cuadrícula-Siges → sucursal-base del PST."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.entities.cuadricula_base_map import CuadriculaBaseMap
from src.modules.liquidaciones.domain.repositories.cuadricula_base_map_repository import (
    CuadriculaBaseMapRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
)


@dataclass(frozen=True)
class CuadriculasPorts:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    cuadricula_maps: CuadriculaBaseMapRepository


@dataclass(frozen=True)
class CuadriculaConMapeo:
    cuadricula: str
    siges_base_sucursal_id: int | None


class ListarCuadriculas:
    """Lista las cuadrículas disponibles en Siges para el PST junto con su
    mapeo de base actual (si existe)."""

    def __init__(self, ports: CuadriculasPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[CuadriculaConMapeo]:
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, prestador_id
        )
        cuadriculas = await self._ports.siges.list_cuadriculas_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        mapeos = {
            m.cuadricula: m.siges_base_sucursal_id
            for m in await self._ports.cuadricula_maps.list_by_prestador(prestador_id)
        }
        return [
            CuadriculaConMapeo(
                cuadricula=c,
                siges_base_sucursal_id=mapeos.get(c),
            )
            for c in cuadriculas
        ]


class MapearCuadricula:
    """Crea o actualiza el mapeo cuadrícula → sucursal base."""

    def __init__(self, ports: CuadriculasPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        prestador_id: UUID,
        cuadricula: str,
        siges_base_sucursal_id: int,
    ) -> CuadriculaBaseMap:
        await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        return await self._ports.cuadricula_maps.upsert(
            prestador_id=prestador_id,
            cuadricula=cuadricula,
            siges_base_sucursal_id=siges_base_sucursal_id,
        )


class EliminarMapeo:
    """Borra el mapeo de una cuadrícula (vuelve a usar la base por defecto)."""

    def __init__(self, ports: CuadriculasPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID, cuadricula: str) -> None:
        await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        await self._ports.cuadricula_maps.delete(
            prestador_id=prestador_id, cuadricula=cuadricula
        )
