"""Validación pura de coordenadas de sucursal para el mapa (Fase 1, sin
geocoding): descarta la basura de carga conocida en `Sucursal.Latitud/
Longitud` sin llamar a ningún servicio externo. Medido 2026-08-22 sobre el
universo real de preventivos: 96.4% de las sucursales pasa (ver diagnóstico de
Fase 0), el resto son placeholders (`0,0`), valores en otro país o longitudes
sin punto decimal — se muestran igual en el mapa marcados como "sin ubicar",
nunca se descartan en silencio."""

import math

# Bbox continental + insular de Argentina (mismo criterio que el Tier 0 de
# geovalidación de liquidaciones, calibrado ahí con muestreo real).
LAT_MIN, LAT_MAX = -55.5, -21.5
LON_MIN, LON_MAX = -73.6, -53.0

# Reconciliación (2026-08-23): si Siges se corrige por afuera de este módulo
# (Siges es de solo lectura acá), su coordenada actual puede terminar cerca
# de una que ya habíamos resuelto por geocoding. En ese caso soltamos el
# override para que Siges vuelva a ser la fuente de verdad en vez de quedar
# tapado para siempre por una corrección vieja.
_UMBRAL_RECONCILIACION_KM = 1.0


def coordenada_valida(latitud: float | None, longitud: float | None) -> bool:
    if latitud is None or longitud is None:
        return False
    if latitud == 0 and longitud == 0:
        return False
    return LAT_MIN <= latitud <= LAT_MAX and LON_MIN <= longitud <= LON_MAX


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rad = math.pi / 180.0
    d_lat = (lat2 - lat1) * rad
    d_lon = (lon2 - lon1) * rad
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(d_lon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def coordenada_reconciliada(
    override_lat: float,
    override_lon: float,
    siges_lat: float | None,
    siges_lon: float | None,
) -> bool:
    if not coordenada_valida(siges_lat, siges_lon):
        return False
    assert siges_lat is not None and siges_lon is not None  # coordenada_valida ya lo garantiza
    distancia = haversine_km(override_lat, override_lon, siges_lat, siges_lon)
    return distancia <= _UMBRAL_RECONCILIACION_KM
