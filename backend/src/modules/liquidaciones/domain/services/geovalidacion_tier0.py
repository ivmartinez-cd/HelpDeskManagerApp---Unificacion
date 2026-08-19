"""Tier 0 de la geovalidación de coordenadas (Fase 2 del plan de matching +
geovalidación): saneo puro, dominio, CERO llamadas a servicios externos.
Filtra antes de gastar nada en Georef/Nominatim/Google — corre sobre TODAS
las sucursales del PST, no solo sobre una muestra.

Deliberadamente NO valida "provincia declarada vs. bounding box provincial"
acá: un bounding box por provincia hardcodeado de memoria es un dato
geográfico de precisión dudosa y el propio plan ya prevé algo mejor y
gratuito para esto en Tier 1 (reverse de Georef contra DesProvincia/
DesCiudad, exacto) — desviación consciente del texto del master prompt,
documentada en docs/liquidaciones/GEOVALIDACION_TABLA_KM.md."""

from dataclasses import dataclass
from typing import Literal

from src.modules.liquidaciones.domain.services.geolocalizacion import haversine_km

Severidad = Literal["alta", "media", "baja"]

# Rectángulo continental + insular grueso (Tierra del Fuego incluida); es un
# filtro de descarte rápido, no una frontera de precisión — casos límite
# reales se confirman después con el reverse de Georef (Tier 1), gratis.
_LAT_MIN_ARG, _LAT_MAX_ARG = -55.5, -21.5
_LON_MIN_ARG, _LON_MAX_ARG = -73.6, -53.0


@dataclass(frozen=True)
class SucursalParaValidar:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    provincia: str | None
    latitud: float | None
    longitud: float | None


@dataclass(frozen=True)
class HallazgoTier0:
    siges_sucursal_id: int
    severidad: Severidad
    codigo: str
    detalle: str


def _en_bbox_argentina(lat: float, lon: float) -> bool:
    return _LAT_MIN_ARG <= lat <= _LAT_MAX_ARG and _LON_MIN_ARG <= lon <= _LON_MAX_ARG


def _coords_invertidas_caen_mejor(lat: float, lon: float) -> bool:
    """Heurística lat/lon permutadas: el par swapeado cae en el país y el
    original no. Solo tiene sentido para pines fuera de Argentina — un pin ya
    válido no se reinterpreta."""
    return _en_bbox_argentina(lon, lat) and not _en_bbox_argentina(lat, lon)


def _evaluar_una(s: SucursalParaValidar) -> HallazgoTier0 | None:
    if s.latitud is None or s.longitud is None:
        return HallazgoTier0(
            s.siges_sucursal_id, "baja", "sin_coordenadas", "Sin pin cargado en Gestión"
        )
    if s.latitud == 0.0 and s.longitud == 0.0:
        return HallazgoTier0(s.siges_sucursal_id, "baja", "sin_coordenadas", "Pin en (0, 0)")
    if _coords_invertidas_caen_mejor(s.latitud, s.longitud):
        return HallazgoTier0(
            s.siges_sucursal_id, "alta", "latlon_invertidas",
            f"({s.latitud}, {s.longitud}) cae fuera de Argentina; invertido cae dentro",
        )
    if not _en_bbox_argentina(s.latitud, s.longitud):
        return HallazgoTier0(
            s.siges_sucursal_id, "alta", "fuera_de_argentina",
            f"({s.latitud}, {s.longitud}) fuera del rectángulo continental+insular",
        )
    return None


def _evaluar_pines_compartidos(sucursales: list[SucursalParaValidar]) -> list[HallazgoTier0]:
    """Mismo pin (redondeado a 5 decimales, ~1 m) compartido por sucursales
    con domicilio distinto — patrón típico de "todas cargadas al centro"."""
    por_pin: dict[tuple[float, float], list[SucursalParaValidar]] = {}
    for s in sucursales:
        if s.latitud is None or s.longitud is None:
            continue
        clave = (round(s.latitud, 5), round(s.longitud, 5))
        por_pin.setdefault(clave, []).append(s)

    hallazgos = []
    for grupo in por_pin.values():
        domicilios = {(s.domicilio or "").strip().lower() for s in grupo}
        if len(grupo) > 1 and len(domicilios) > 1:
            for s in grupo:
                hallazgos.append(HallazgoTier0(
                    s.siges_sucursal_id, "media", "pin_compartido",
                    f"Mismo pin que otras {len(grupo) - 1} sucursal(es) con domicilio distinto",
                ))
    return hallazgos


def _evaluar_distancia_base(
    sucursales: list[SucursalParaValidar], base: tuple[float, float], umbral_km: float
) -> list[HallazgoTier0]:
    hallazgos = []
    for s in sucursales:
        if s.latitud is None or s.longitud is None:
            continue
        distancia = haversine_km(base[0], base[1], s.latitud, s.longitud)
        if distancia > umbral_km:
            hallazgos.append(HallazgoTier0(
                s.siges_sucursal_id, "media", "lejos_de_base",
                f"{distancia:.0f} km de la base de despacho (umbral {umbral_km:.0f} km)",
            ))
    return hallazgos


def evaluar_tier0(
    sucursales: list[SucursalParaValidar],
    base: tuple[float, float] | None = None,
    umbral_distancia_base_km: float = 300.0,
) -> list[HallazgoTier0]:
    """Corre las 5 reglas de Tier 0 sobre TODAS las sucursales del PST. Una
    sucursal puede tener más de un hallazgo. `umbral_distancia_base_km` es
    provisorio (300 km, sin evidencia calibrada todavía) — a ajustar en la
    medición real por PST antes de usarlo para descartar casos."""
    hallazgos = [h for s in sucursales if (h := _evaluar_una(s)) is not None]
    hallazgos.extend(_evaluar_pines_compartidos(sucursales))
    if base is not None:
        hallazgos.extend(_evaluar_distancia_base(sucursales, base, umbral_distancia_base_km))
    return hallazgos
