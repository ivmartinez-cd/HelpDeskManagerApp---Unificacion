"""FijarPinManual — coordenadas verificadas a mano (o por un agente con
evidencia) para una sucursal de Siges, tenga o no pin: crea/actualiza el
override en `sucursal_coordenadas` con procedencia `manual` y guarda la fuente
en `formatted_address` para que quede rastro de dónde salió el dato.

Nace del pelotón de geolocalización 2026-09-05: los 141 pines "rotos en
Gestión" (pin en California o en el centroide del país, geocode impreciso) no
tenían forma de corregirse acá — `ResolverCoordenadas` exige una fila previa y
`CorregirPin` solo aplica el geocode cacheado. Valida que la sucursal exista
en Siges para ese prestador y que las coordenadas caigan en Argentina."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.liquidaciones.domain.errors import PinManualInvalidoError
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.liquidaciones.domain.services.geolocalizacion import (
    PROCEDENCIA_MANUAL,
    armar_direccion,
)

# Caja de Argentina continental + Tierra del Fuego (grados decimales).
_LAT = (-55.5, -21.5)
_LON = (-74.0, -53.0)


@dataclass(frozen=True)
class FijarPinManualPorts:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    sucursal_coords: SucursalCoordenadasRepository


class FijarPinManual:
    def __init__(self, ports: FijarPinManualPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        prestador_id: UUID,
        siges_sucursal_id: int,
        *,
        latitud: float,
        longitud: float,
        fuente: str,
    ) -> SucursalCoordenadas:
        _validar_coords(latitud, longitud)
        if not fuente.strip():
            raise PinManualInvalidoError("Indicá la fuente de las coordenadas")
        sucursal = await self._buscar_sucursal(prestador_id, siges_sucursal_id)
        return await self._guardar(prestador_id, sucursal, latitud, longitud, fuente)

    async def _buscar_sucursal(
        self, prestador_id: UUID, siges_sucursal_id: int
    ) -> SigesSucursalCliente:
        prestador = await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        sucursal = next((s for s in sucursales if s.siges_sucursal_id == siges_sucursal_id), None)
        if sucursal is None:
            raise PinManualInvalidoError(f"Sucursal {siges_sucursal_id} no es de este prestador")
        return sucursal

    async def _guardar(
        self,
        prestador_id: UUID,
        sucursal: SigesSucursalCliente,
        latitud: float,
        longitud: float,
        fuente: str,
    ) -> SucursalCoordenadas:
        await self._registrar_pendiente(prestador_id, sucursal)
        resuelta = await self._ports.sucursal_coords.resolver(
            siges_sucursal_id=sucursal.siges_sucursal_id,
            latitud=latitud,
            longitud=longitud,
            procedencia=PROCEDENCIA_MANUAL,
            formatted_address=fuente.strip()[:500],
        )
        if resuelta is None:
            raise PinManualInvalidoError("No se pudo guardar la resolución")
        return resuelta

    async def _registrar_pendiente(
        self, prestador_id: UUID, sucursal: SigesSucursalCliente
    ) -> None:
        await self._ports.sucursal_coords.upsert_pendiente(
            prestador_id=prestador_id,
            siges_sucursal_id=sucursal.siges_sucursal_id,
            empresa_nombre=sucursal.empresa_nombre,
            sucursal_nombre=sucursal.sucursal_nombre,
            direccion_normalizada=armar_direccion(
                sucursal.domicilio, sucursal.localidad, sucursal.provincia
            ),
        )


def _validar_coords(latitud: float, longitud: float) -> None:
    if not (_LAT[0] <= latitud <= _LAT[1] and _LON[0] <= longitud <= _LON[1]):
        raise PinManualInvalidoError(f"Coordenadas fuera de Argentina: {latitud}, {longitud}")
