"""Detección cruzada de pines no confiables — dos patrones, mismo espíritu
que el Tier 0 de geovalidación de liquidaciones: comparar la coordenada de
una sucursal contra las de OTRAS sucursales para encontrar lo que un chequeo
por-fila (domain/services/coordenadas.py) no puede ver.

- `detectar_pines_compartidos`: mismo punto exacto, domicilio distinto —
  típico pin genérico de ciudad/departamento reusado. Medido 2026-08-23:
  698 de 4660 sucursales "válidas" (bbox OK).
- `detectar_domicilios_en_conflicto`: mismo domicilio, pines que difieren de
  verdad entre sí — varias sucursales en la misma dirección real (ej. un
  shopping) con Latitud/Longitud cargadas por separado y a mano, sin
  consistencia. Caso real que disparó esta auditoría: tres locales en
  "Av. Constituyentes 6020" con pines a ~1.5km entre sí."""

import math

from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalParaGeocoding

# Redondeo a 5 decimales (~1m): coincidencia exacta, no cercanía — dos
# sucursales vecinas de verdad no deben marcarse por estar a metros.
_PRECISION_DECIMALES = 5

# Sucursales con el mismo domicilio real están, por definición, en el mismo
# lugar: una diferencia mayor a esto entre sus pines es un dato mal cargado,
# no ruido de GPS.
_UMBRAL_CONFLICTO_KM = 0.8


def detectar_pines_compartidos(sucursales: list[SucursalParaGeocoding]) -> set[int]:
    por_coordenada: dict[tuple[float, float], list[SucursalParaGeocoding]] = {}
    for s in sucursales:
        if s.latitud is None or s.longitud is None:
            continue
        clave = (round(s.latitud, _PRECISION_DECIMALES), round(s.longitud, _PRECISION_DECIMALES))
        por_coordenada.setdefault(clave, []).append(s)

    sospechosos: set[int] = set()
    for grupo in por_coordenada.values():
        if len(grupo) < 2:
            continue
        if len({s.domicilio for s in grupo}) > 1:
            sospechosos.update(s.id_sucursal for s in grupo)
    return sospechosos


def detectar_domicilios_en_conflicto(sucursales: list[SucursalParaGeocoding]) -> set[int]:
    por_domicilio: dict[tuple[str, str], list[SucursalParaGeocoding]] = {}
    for s in sucursales:
        if s.latitud is None or s.longitud is None or not s.domicilio.strip():
            continue
        clave = (s.domicilio.strip().lower(), s.ciudad.strip().lower())
        por_domicilio.setdefault(clave, []).append(s)

    sospechosos: set[int] = set()
    for grupo in por_domicilio.values():
        if len(grupo) >= 2 and _hay_conflicto(grupo):
            sospechosos.update(s.id_sucursal for s in grupo)
    return sospechosos


def _hay_conflicto(grupo: list[SucursalParaGeocoding]) -> bool:
    base_lat, base_lon = grupo[0].latitud, grupo[0].longitud
    assert base_lat is not None and base_lon is not None  # filtrado al armar el grupo
    for otro in grupo[1:]:
        assert otro.latitud is not None and otro.longitud is not None
        if _haversine_km(base_lat, base_lon, otro.latitud, otro.longitud) > _UMBRAL_CONFLICTO_KM:
            return True
    return False


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rad = math.pi / 180.0
    d_lat = (lat2 - lat1) * rad
    d_lon = (lon2 - lon1) * rad
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(d_lon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(a))
