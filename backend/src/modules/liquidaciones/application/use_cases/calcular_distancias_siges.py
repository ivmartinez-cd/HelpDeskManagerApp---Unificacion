"""Cálculo de distancias PST↔sucursal en dos pasos (preview → apply).

El preview llama a Google (ida y vuelta reales por destino) y persiste la
propuesta SIN tocar tabla_km; el apply materializa esa propuesta sin volver a
llamar a Google. Convención Fase 0 (2026-08-15): `kms_recorrido` y
`kms_a_facturar` son el TOTAL ida+vuelta; `umbral_viatico` se compara contra
ese total y NUNCA se pisa en filas existentes (tampoco `observaciones`).

Destinos: coords de Siges cuando existen (`coords_origen='siges'`); si no, la
resolución local de `sucursal_coordenadas` (geocode confirmado o manual). Una
sucursal sin ninguna de las dos queda contada en `sin_ubicar` — jamás se
inventa una coordenada."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    Destino,
    calcular_kms_a_facturar,
    maps_url_ida_vuelta,
    obtener_coords_base,
    parse_latlon_siges,
    validar_prestador_para_distancias,
    verificar_tope,
)
from src.modules.liquidaciones.domain.entities.calculo_km_preview import (
    ACCION_ACTUALIZAR,
    ACCION_CREAR,
    CalculoKmPreview,
    PreviewFila,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.liquidaciones.domain.entities.tabla_km import UMBRAL_VIATICO_DEFAULT, TablaKm
from src.modules.liquidaciones.domain.errors import PreviewNoEncontradoError
from src.modules.liquidaciones.domain.repositories.calculo_km_preview_repository import (
    CalculoKmPreviewRepository,
)
from src.modules.liquidaciones.domain.repositories.google_maps_gateway import GoogleMapsGateway
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.geolocalizacion import (
    PROCEDENCIA_MANUAL,
    PROCEDENCIA_SIGES,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre

_GOOGLE_BATCH = 25


@dataclass(frozen=True)
class CalcularDistanciasPorts:
    prestadores: PrestadorRepository
    tabla_km: TablaKmRepository
    siges: SigesCatalogoGateway
    google_maps: GoogleMapsGateway
    sucursal_coords: SucursalCoordenadasRepository
    previews: CalculoKmPreviewRepository


@dataclass(frozen=True)
class AplicarDistanciasResultado:
    creadas: int
    actualizadas: int


class PreviewCalcularDistancias:
    def __init__(self, ports: CalcularDistanciasPorts, tope_llamadas: int) -> None:
        self._ports = ports
        self._tope = tope_llamadas

    async def execute(self, prestador_id: UUID) -> CalculoKmPreview:
        prestador = await validar_prestador_para_distancias(
            self._ports.prestadores, prestador_id
        )
        base = await obtener_coords_base(self._ports.siges, prestador)
        destinos, sin_ubicar = await self._armar_destinos(prestador)
        verificar_tope(2 * len(destinos), self._tope)
        existentes = await self._cargar_existentes(prestador_id)
        filas, sin_ruta = await self._calcular_filas(base, destinos, existentes)
        return await self._ports.previews.create(
            prestador_id=prestador_id,
            filas=tuple(filas),
            sin_ubicar=sin_ubicar,
            sin_ruta=sin_ruta,
            elementos_google=2 * len(destinos),
        )

    async def _armar_destinos(self, prestador: Prestador) -> tuple[list[Destino], int]:
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        resoluciones = {
            r.siges_sucursal_id: r
            for r in await self._ports.sucursal_coords.list_by_prestador(prestador.id)
            if r.resuelta
        }
        destinos: list[Destino] = []
        sin_ubicar = 0
        for s in sucursales:
            destino = _resolver_destino(s, resoluciones)
            if destino is None:
                sin_ubicar += 1
            else:
                destinos.append(destino)
        return destinos, sin_ubicar

    async def _cargar_existentes(self, prestador_id: UUID) -> dict[tuple[str, str], TablaKm]:
        return {
            (normalizar_nombre(f.empresa_nombre), normalizar_nombre(f.sucursal_nombre)): f
            for f in await self._ports.tabla_km.list_by_prestador(prestador_id)
        }

    async def _calcular_filas(
        self,
        base: tuple[float, float],
        destinos: list[Destino],
        existentes: dict[tuple[str, str], TablaKm],
    ) -> tuple[list[PreviewFila], int]:
        filas: list[PreviewFila] = []
        sin_ruta = 0
        for i in range(0, len(destinos), _GOOGLE_BATCH):
            batch = destinos[i : i + _GOOGLE_BATCH]
            tramos = await self._ports.google_maps.distancias_km_ida_vuelta(
                base, [d.coords for d in batch]
            )
            for destino, (ida, vuelta) in zip(batch, tramos, strict=True):
                if ida is None or vuelta is None:
                    sin_ruta += 1
                    continue
                filas.append(_armar_fila(destino, ida, vuelta, existentes))
        return filas, sin_ruta


class AplicarCalcularDistancias:
    def __init__(self, ports: CalcularDistanciasPorts) -> None:
        self._ports = ports

    async def execute(self, preview_id: UUID) -> AplicarDistanciasResultado:
        preview = await self._ports.previews.get_by_id(preview_id)
        if preview is None:
            raise PreviewNoEncontradoError(preview_id)
        prestador = await validar_prestador_para_distancias(
            self._ports.prestadores, preview.prestador_id
        )
        base = await obtener_coords_base(self._ports.siges, prestador)
        creadas = actualizadas = 0
        for fila in preview.filas:
            c, a = await self._aplicar_fila(preview.prestador_id, base, fila)
            creadas += c
            actualizadas += a
        await self._ports.previews.delete(preview_id)
        return AplicarDistanciasResultado(creadas=creadas, actualizadas=actualizadas)

    async def _aplicar_fila(
        self, prestador_id: UUID, base: tuple[float, float], fila: PreviewFila
    ) -> tuple[int, int]:
        url = maps_url_ida_vuelta(base, (fila.latitud_destino, fila.longitud_destino))
        if fila.accion == ACCION_ACTUALIZAR and fila.tabla_km_id is not None:
            actualizada = await self._ports.tabla_km.update_distancias(
                fila.tabla_km_id,
                kms_ida=fila.kms_ida,
                kms_vuelta=fila.kms_vuelta,
                kms_recorrido=fila.kms_total,
                aplica_viatico=fila.aplica_viatico,
                kms_a_facturar=fila.kms_a_facturar,
                url_maps=url,
                latitud_destino=fila.latitud_destino,
                longitud_destino=fila.longitud_destino,
                coords_origen=fila.coords_origen,
            )
            return (0, 1) if actualizada else (0, 0)
        await self._crear_fila(prestador_id, fila, url)
        return 1, 0

    async def _crear_fila(self, prestador_id: UUID, fila: PreviewFila, url: str) -> None:
        await self._ports.tabla_km.create(
            prestador_id=prestador_id,
            spst_id=None,
            empresa_nombre=fila.empresa_nombre,
            sucursal_nombre=fila.sucursal_nombre,
            observaciones=None,
            domicilio_cliente=fila.domicilio,
            localidad_cliente=fila.localidad,
            provincia_cliente=fila.provincia,
            kms_recorrido=fila.kms_total,
            umbral_viatico=fila.umbral_viatico,
            aplica_viatico=fila.aplica_viatico,
            kms_a_facturar=fila.kms_a_facturar,
            url_maps=url,
            latitud_destino=fila.latitud_destino,
            longitud_destino=fila.longitud_destino,
            kms_ida=fila.kms_ida,
            kms_vuelta=fila.kms_vuelta,
            coords_origen=fila.coords_origen,
        )


def _resolver_destino(
    sucursal: SigesSucursalCliente, resoluciones: dict[int, SucursalCoordenadas]
) -> Destino | None:
    coords = parse_latlon_siges(sucursal.latitud, sucursal.longitud)
    if coords is not None:
        return Destino(sucursal=sucursal, coords=coords, coords_origen=PROCEDENCIA_SIGES)
    resolucion = resoluciones.get(sucursal.siges_sucursal_id)
    if resolucion is None or resolucion.latitud is None or resolucion.longitud is None:
        return None
    return Destino(
        sucursal=sucursal,
        coords=(resolucion.latitud, resolucion.longitud),
        coords_origen=resolucion.procedencia or PROCEDENCIA_MANUAL,
    )


def _armar_fila(
    destino: Destino,
    ida: float,
    vuelta: float,
    existentes: dict[tuple[str, str], TablaKm],
) -> PreviewFila:
    s = destino.sucursal
    key = (normalizar_nombre(s.empresa_nombre), normalizar_nombre(s.sucursal_nombre))
    existente = existentes.get(key)
    total = round(ida + vuelta, 3)
    umbral = existente.umbral_viatico if existente else UMBRAL_VIATICO_DEFAULT
    aplica, kms_a_facturar = calcular_kms_a_facturar(total, umbral)
    return PreviewFila(
        accion=ACCION_ACTUALIZAR if existente else ACCION_CREAR,
        tabla_km_id=existente.id if existente else None,
        siges_sucursal_id=s.siges_sucursal_id,
        empresa_nombre=existente.empresa_nombre if existente else s.empresa_nombre,
        sucursal_nombre=existente.sucursal_nombre if existente else s.sucursal_nombre,
        domicilio=s.domicilio,
        localidad=s.localidad,
        provincia=s.provincia,
        coords_origen=destino.coords_origen,
        latitud_destino=destino.coords[0],
        longitud_destino=destino.coords[1],
        kms_ida=round(ida, 3),
        kms_vuelta=round(vuelta, 3),
        kms_total=total,
        umbral_viatico=umbral,
        aplica_viatico=aplica,
        kms_a_facturar=kms_a_facturar,
        kms_recorrido_actual=existente.kms_recorrido if existente else None,
        kms_a_facturar_actual=existente.kms_a_facturar if existente else None,
    )
