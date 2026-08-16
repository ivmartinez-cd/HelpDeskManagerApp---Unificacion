"""Alta asistida de Tabla KM (ADR-014, dataset 3): búsqueda de sucursales del
PST en Siges para prefillar el formulario de alta.

Solo lectura por diseño — este caso de uso NUNCA escribe: no crea, no pisa y no
borra filas de Tabla KM (los pares existentes, migrados del legacy, quedan
intactos). El alta real sigue siendo la decisión manual del usuario vía
`CreateTablaKm`, y el km esperado es siempre dato manual (no existe en Siges).
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.siges_sucursales import SucursalSigesDTO
from src.modules.liquidaciones.domain.errors import (
    PrestadorNoEncontradoError,
    PrestadorSinVinculoSigesError,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalPropia,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre


@dataclass(frozen=True)
class SigesSucursalesPropiasSimplePorts:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway


class ListarSucursalesPropias:
    """Lista sucursales propias (sedes) del PST para el selector de base."""

    def __init__(self, ports: SigesSucursalesPropiasSimplePorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[SigesSucursalPropia]:
        prestador = await self._ports.prestadores.get_by_id(prestador_id)
        if prestador is None:
            raise PrestadorNoEncontradoError(prestador_id)
        if prestador.siges_empresa_id is None:
            raise PrestadorSinVinculoSigesError(prestador_id)
        return await self._ports.siges.list_sucursales_de_empresa(prestador.siges_empresa_id)


@dataclass(frozen=True)
class SigesSucursalesPorts:
    prestadores: PrestadorRepository
    tabla_km: TablaKmRepository
    siges: SigesCatalogoGateway


class BuscarSucursalesSiges:
    def __init__(self, ports: SigesSucursalesPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID, *, q: str) -> list[SucursalSigesDTO]:
        prestador = await self._ports.prestadores.get_by_id(prestador_id)
        if prestador is None:
            raise PrestadorNoEncontradoError(prestador_id)
        if prestador.siges_empresa_id is None:
            raise PrestadorSinVinculoSigesError(prestador_id)

        cargadas = {
            (normalizar_nombre(fila.empresa_nombre), normalizar_nombre(fila.sucursal_nombre))
            for fila in await self._ports.tabla_km.list_by_prestador(prestador_id)
        }
        filtro = normalizar_nombre(q)
        resultados = []
        for sucursal in await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id
        ):
            empresa = normalizar_nombre(sucursal.empresa_nombre)
            nombre = normalizar_nombre(sucursal.sucursal_nombre)
            if filtro and filtro not in empresa and filtro not in nombre:
                continue
            resultados.append(
                SucursalSigesDTO(
                    siges_sucursal_id=sucursal.siges_sucursal_id,
                    empresa_nombre=sucursal.empresa_nombre,
                    sucursal_nombre=sucursal.sucursal_nombre,
                    domicilio=sucursal.domicilio,
                    localidad=sucursal.localidad,
                    provincia=sucursal.provincia,
                    ya_cargada=(empresa, nombre) in cargadas,
                )
            )
        return resultados
