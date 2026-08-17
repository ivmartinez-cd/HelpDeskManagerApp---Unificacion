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
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, prestador_id
        )
        sucursales_siges = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        indice = {
            (normalizar_nombre(s.empresa_nombre), normalizar_nombre(s.sucursal_nombre)): s
            for s in sucursales_siges
        }
        filas = await self._ports.tabla_km.list_by_prestador(prestador_id)
        actualizadas = sin_cambios = no_encontradas = 0
        cambios: list[CambioDomicilio] = []
        no_encontradas_detalle: list[FilaNoEncontrada] = []
        for fila in filas:
            key = (normalizar_nombre(fila.empresa_nombre), normalizar_nombre(fila.sucursal_nombre))
            siges = indice.get(key)
            if siges is None:
                no_encontradas += 1
                no_encontradas_detalle.append(
                    FilaNoEncontrada(
                        empresa_nombre=fila.empresa_nombre,
                        sucursal_nombre=fila.sucursal_nombre,
                    )
                )
                continue
            if _mismo_domicilio(fila, siges.domicilio, siges.localidad, siges.provincia):
                sin_cambios += 1
                continue
            cambios.append(CambioDomicilio(
                sucursal_nombre=fila.sucursal_nombre,
                empresa_nombre=fila.empresa_nombre,
                domicilio_antes=fila.domicilio_cliente,
                domicilio_despues=siges.domicilio,
            ))
            await self._ports.tabla_km.update_domicilio(
                fila.id,
                domicilio_cliente=siges.domicilio,
                localidad_cliente=siges.localidad,
                provincia_cliente=siges.provincia,
                siges_sucursal_id=siges.siges_sucursal_id,
                id_costo_servicios=siges.id_costo_servicios,
            )
            actualizadas += 1
        return RefrescarDireccionesResultado(
            actualizadas=actualizadas,
            sin_cambios=sin_cambios,
            no_encontradas=no_encontradas,
            cambios=cambios,
            no_encontradas_detalle=no_encontradas_detalle,
        )


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
