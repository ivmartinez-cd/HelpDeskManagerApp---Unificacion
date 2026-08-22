"""Validación pura de coordenadas de sucursal para el mapa (Fase 1, sin
geocoding): descarta la basura de carga conocida en `Sucursal.Latitud/
Longitud` sin llamar a ningún servicio externo. Medido 2026-08-22 sobre el
universo real de preventivos: 96.4% de las sucursales pasa (ver diagnóstico de
Fase 0), el resto son placeholders (`0,0`), valores en otro país o longitudes
sin punto decimal — se muestran igual en el mapa marcados como "sin ubicar",
nunca se descartan en silencio."""

# Bbox continental + insular de Argentina (mismo criterio que el Tier 0 de
# geovalidación de liquidaciones, calibrado ahí con muestreo real).
LAT_MIN, LAT_MAX = -55.5, -21.5
LON_MIN, LON_MAX = -73.6, -53.0


def coordenada_valida(latitud: float | None, longitud: float | None) -> bool:
    if latitud is None or longitud is None:
        return False
    if latitud == 0 and longitud == 0:
        return False
    return LAT_MIN <= latitud <= LAT_MAX and LON_MIN <= longitud <= LON_MAX
