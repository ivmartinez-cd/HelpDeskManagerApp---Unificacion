"""Preview del cálculo de distancias PST↔sucursal (paso 1 de 2, ver
`aplicar_calcular_distancias.py` para el paso 2 — separados porque juntos
superaban el tamaño máximo de archivo, §4).

El preview llama a Google (ida y vuelta reales por destino) y persiste la
propuesta SIN tocar tabla_km. Convención Fase 0 (2026-08-15): `kms_recorrido`
y `kms_a_facturar` son el TOTAL ida+vuelta; `umbral_viatico` se compara contra
ese total y NUNCA se pisa en filas existentes (tampoco `observaciones`).

Destinos: coords de Siges cuando existen (`coords_origen='siges'`); si no, la
resolución local de `sucursal_coordenadas` (geocode confirmado o manual). Una
sucursal sin ninguna de las dos queda contada en `sin_ubicar`.

Base multi-sede: cada cliente tiene `IDCostoServicios` en Siges; el mismo campo
está en las sucursales PROPIAS del PST (`Id_Empresa = empresa_id`). Si coinciden,
el destino sale desde esa base propia; si no hay match, usa la base por defecto
del prestador. El `latitud_base`/`longitud_base` de cada `PreviewFila` registra
qué base se usó (confirmado en PST SAN JUAN y INFOMAC, 2026-08-16)."""

from collections import defaultdict
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    CalcularDistanciasPorts,
    Destino,
    build_costo_bases,
    calcular_kms_a_facturar,
    coords_base_default,
    desde_periodo_hace_meses,
    es_empresa_activa,
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
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.geolocalizacion import (
    PROCEDENCIA_MANUAL,
    PROCEDENCIA_SIGES,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre

_GOOGLE_BATCH = 25


class PreviewCalcularDistancias:
    def __init__(self, ports: CalcularDistanciasPorts, tope_llamadas: int) -> None:
        self._ports = ports
        self._tope = tope_llamadas

    async def execute(self, prestador_id: UUID) -> CalculoKmPreview:
        prestador = await validar_prestador_para_distancias(
            self._ports.prestadores, prestador_id
        )
        propias = await self._ports.siges.list_sucursales_de_empresa(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        base_default = coords_base_default(prestador, propias)
        costo_bases = build_costo_bases(propias)
        destinos, sin_ubicar, sin_actividad = await self._armar_destinos(prestador)
        verificar_tope(2 * len(destinos), self._tope)
        existentes = await self._cargar_existentes(prestador_id)
        filas, sin_ruta = await self._calcular_filas(
            base_default, costo_bases, destinos, existentes
        )
        return await self._ports.previews.create(
            prestador_id=prestador_id,
            filas=tuple(filas),
            sin_ubicar=sin_ubicar,
            sin_ruta=sin_ruta,
            elementos_google=2 * len(destinos),
            sin_actividad=sin_actividad,
        )

    async def _armar_destinos(self, prestador: Prestador) -> tuple[list[Destino], int, int]:
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        activos_raw = await self._ports.incidentes.empresas_con_actividad_reciente(
            prestador.id, desde_periodo_hace_meses(24)
        )
        activos_norm = {normalizar_nombre(n) for n in activos_raw}
        resoluciones = {
            r.siges_sucursal_id: r
            for r in await self._ports.sucursal_coords.list_by_prestador(prestador.id)
            if r.resuelta
        }
        destinos: list[Destino] = []
        sin_ubicar = 0
        sin_actividad = 0
        for s in sucursales:
            if not es_empresa_activa(s.empresa_nombre, activos_norm):
                sin_actividad += 1
                continue
            destino = _resolver_destino(s, resoluciones)
            if destino is None:
                sin_ubicar += 1
            else:
                destinos.append(destino)
        return destinos, sin_ubicar, sin_actividad

    async def _cargar_existentes(self, prestador_id: UUID) -> dict[tuple[str, str], TablaKm]:
        return {
            (normalizar_nombre(f.empresa_nombre), normalizar_nombre(f.sucursal_nombre)): f
            for f in await self._ports.tabla_km.list_by_prestador(prestador_id)
        }

    async def _calcular_filas(
        self,
        base_default: tuple[float, float],
        costo_bases: dict[int, tuple[float, float]],
        destinos: list[Destino],
        existentes: dict[tuple[str, str], TablaKm],
    ) -> tuple[list[PreviewFila], int]:
        # Agrupar destinos por base efectiva para minimizar batches distintos.
        grupos: dict[tuple[float, float], list[Destino]] = defaultdict(list)
        for d in destinos:
            id_cs = d.sucursal.id_costo_servicios
            base = (costo_bases.get(id_cs) if id_cs is not None else None) or base_default
            grupos[base].append(d)

        filas: list[PreviewFila] = []
        sin_ruta = 0
        for base, grupo in grupos.items():
            for i in range(0, len(grupo), _GOOGLE_BATCH):
                sin_ruta += await self._procesar_batch(
                    base, grupo[i : i + _GOOGLE_BATCH], existentes, filas
                )
        return filas, sin_ruta

    async def _procesar_batch(
        self,
        base: tuple[float, float],
        batch: list[Destino],
        existentes: dict[tuple[str, str], TablaKm],
        filas: list[PreviewFila],
    ) -> int:
        """Un pedido de matrix por batch; suma filas al preview y devuelve
        cuántos destinos quedaron sin ruta."""
        tramos = await self._ports.google_maps.distancias_km_ida_vuelta(
            base, [d.coords for d in batch]
        )
        sin_ruta = 0
        for destino, (ida, vuelta) in zip(batch, tramos, strict=True):
            if ida is None or vuelta is None:
                sin_ruta += 1
                continue
            filas.append(_armar_fila(destino, base, ida, vuelta, existentes))
        return sin_ruta


def _resolver_destino(
    sucursal: SigesSucursalCliente, resoluciones: dict[int, SucursalCoordenadas]
) -> Destino | None:
    # Override explícito (corrección de pin sospechoso) tiene prioridad sobre Siges.
    resolucion = resoluciones.get(sucursal.siges_sucursal_id)
    if resolucion is not None:
        lat, lon = resolucion.latitud, resolucion.longitud
        if lat is not None and lon is not None:
            return Destino(
                sucursal=sucursal,
                coords=(lat, lon),
                coords_origen=resolucion.procedencia or PROCEDENCIA_MANUAL,
            )
    coords = parse_latlon_siges(sucursal.latitud, sucursal.longitud)
    if coords is not None:
        return Destino(sucursal=sucursal, coords=coords, coords_origen=PROCEDENCIA_SIGES)
    return None


def _armar_fila(
    destino: Destino,
    base: tuple[float, float],
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
        latitud_base=base[0],
        longitud_base=base[1],
        kms_ida=round(ida, 3),
        kms_vuelta=round(vuelta, 3),
        kms_total=total,
        umbral_viatico=umbral,
        aplica_viatico=aplica,
        kms_a_facturar=kms_a_facturar,
        kms_recorrido_actual=existente.kms_recorrido if existente else None,
        kms_a_facturar_actual=existente.kms_a_facturar if existente else None,
        id_costo_servicios=s.id_costo_servicios,
    )
