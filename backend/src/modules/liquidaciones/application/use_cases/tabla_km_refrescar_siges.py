"""Refresco masivo de domicilios de Tabla KM desde Siges (matcheo por nombre
normalizado). Separado de tabla_km_lugares: esto es un sync de datos maestros,
no una operación por fila."""

from dataclasses import dataclass, field
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.application.use_cases.tabla_km_lugares import (
    TablaKmLugaresPorts,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre


@dataclass(frozen=True)
class CambioDomicilio:
    sucursal_nombre: str
    empresa_nombre: str
    domicilio_antes: str | None
    domicilio_despues: str | None


@dataclass(frozen=True)
class FilaNoEncontrada:
    empresa_nombre: str
    sucursal_nombre: str


@dataclass(frozen=True)
class RefrescarDireccionesResultado:
    actualizadas: int
    sin_cambios: int
    no_encontradas: int
    cambios: list[CambioDomicilio] = field(default_factory=list)
    no_encontradas_detalle: list[FilaNoEncontrada] = field(default_factory=list)


class RefrescarDatosSiges:
    """Sincroniza domicilio/localidad/provincia de las filas de tabla_km con
    Siges, matcheando por nombre normalizado. Filas sin match se reportan pero
    no se tocan — puede ocurrir si el nombre cambió en Gestión."""

    def __init__(self, ports: TablaKmLugaresPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> RefrescarDireccionesResultado:
        indice = await self._indice_siges(prestador_id)
        filas = await self._ports.tabla_km.list_by_prestador(prestador_id)
        sin_cambios = 0
        cambios: list[CambioDomicilio] = []
        no_encontradas: list[FilaNoEncontrada] = []
        for fila in filas:
            siges = indice.get(_clave_nombre(fila.empresa_nombre, fila.sucursal_nombre))
            if siges is None:
                no_encontradas.append(FilaNoEncontrada(
                    empresa_nombre=fila.empresa_nombre,
                    sucursal_nombre=fila.sucursal_nombre,
                ))
            elif _mismo_domicilio(fila, siges.domicilio, siges.localidad, siges.provincia):
                sin_cambios += 1
            else:
                cambios.append(await self._actualizar_fila(fila, siges))
        return RefrescarDireccionesResultado(
            actualizadas=len(cambios),
            sin_cambios=sin_cambios,
            no_encontradas=len(no_encontradas),
            cambios=cambios,
            no_encontradas_detalle=no_encontradas,
        )

    async def _indice_siges(
        self, prestador_id: UUID
    ) -> dict[tuple[str, str], SigesSucursalCliente]:
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, prestador_id
        )
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        return {_clave_nombre(s.empresa_nombre, s.sucursal_nombre): s for s in sucursales}

    async def _actualizar_fila(
        self, fila: TablaKm, siges: SigesSucursalCliente
    ) -> CambioDomicilio:
        await self._ports.tabla_km.update_domicilio(
            fila.id,
            domicilio_cliente=siges.domicilio,
            localidad_cliente=siges.localidad,
            provincia_cliente=siges.provincia,
            siges_sucursal_id=siges.siges_sucursal_id,
            id_costo_servicios=siges.id_costo_servicios,
        )
        return CambioDomicilio(
            sucursal_nombre=fila.sucursal_nombre,
            empresa_nombre=fila.empresa_nombre,
            domicilio_antes=fila.domicilio_cliente,
            domicilio_despues=siges.domicilio,
        )


def _clave_nombre(empresa: str, sucursal: str) -> tuple[str, str]:
    return (normalizar_nombre(empresa), normalizar_nombre(sucursal))


def _mismo_domicilio(
    fila: TablaKm,
    domicilio: str | None,
    localidad: str | None,
    provincia: str | None,
) -> bool:
    return (
        fila.domicilio_cliente == domicilio
        and fila.localidad_cliente == localidad
        and fila.provincia_cliente == provincia
    )
