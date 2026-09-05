"""Normalización de direcciones Siges, elección de candidato de geocode y
discrepancia pin-vs-geocode. Dominio puro: sin llamadas a Google.

Calibrado con el muestreo real 2026-08-15 (n=20): el geocode urbano argentino da
mediana 22 m; las direcciones rurales "Ruta X KM Y" devuelven GEOMETRIC_CENTER
de la ruta entera (5-330 km de error), así que solo se auto-resuelve un match
preciso e inequívoco — el resto queda para revisión humana."""

import math
import re

from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato

UMBRAL_PIN_SOSPECHOSO_KM = 5.0

# Procedencia de coordenadas — compartida por TablaKm.coords_origen y
# SucursalCoordenadas.procedencia (mismos valores, campos distintos en
# entidades distintas).
PROCEDENCIA_SIGES = "siges"
PROCEDENCIA_GEOCODE = "geocode"
PROCEDENCIA_MANUAL = "manual"

# Los domicilios de Siges arrastran sufijos de formulario vacíos ("Piso: Dpto:",
# "Piso:7 Dpto:") y un " 0" final de altura sin dato — ruido para el geocoder.
_SUFIJO_PISO = re.compile(r"\s*Piso\s*:.*$", re.IGNORECASE)
_ALTURA_CERO = re.compile(r"\s+0$")

_LOCATION_TYPES_PRECISOS = ("ROOFTOP", "RANGE_INTERPOLATED")
_RADIO_TIERRA_KM = 6371.0


def normalizar_domicilio(domicilio: str) -> str:
    limpio = _SUFIJO_PISO.sub("", domicilio).strip()
    limpio = _ALTURA_CERO.sub("", limpio).strip(" ,")
    return "" if limpio == "0" else limpio


def armar_direccion(
    domicilio: str | None, localidad: str | None, provincia: str | None
) -> str | None:
    """Query de geocode `domicilio, localidad, provincia, Argentina`. `None` si
    no hay ni domicilio ni localidad (no tiene sentido geocodificar solo la
    provincia)."""
    partes = []
    dom_norm = normalizar_domicilio(domicilio) if domicilio else ""
    if dom_norm:
        partes.append(dom_norm)
    if localidad and localidad.strip():
        partes.append(localidad.strip())
    if not partes:
        return None
    if provincia and provincia.strip():
        partes.append(provincia.strip())
    partes.append("Argentina")
    return ", ".join(partes)


def armar_busqueda_por_nombre(
    empresa: str | None, sucursal: str | None, localidad: str | None, provincia: str | None
) -> str | None:
    """Segundo intento cuando el domicilio no geocodifica: buscar el punto de
    interés por nombre ("OCA Santa Rosa", "Aeropuerto de Bahía Blanca") en la
    localidad. `None` sin nombre o sin localidad — sin localidad la búsqueda por
    marca devuelve cualquier sucursal del país."""
    nombre = " ".join(p.strip() for p in (empresa or "", sucursal or "") if p and p.strip())
    if not nombre or not (localidad and localidad.strip()):
        return None
    partes = [nombre, localidad.strip()]
    if provincia and provincia.strip():
        partes.append(provincia.strip())
    partes.append("Argentina")
    return ", ".join(partes)


def elegir_automatico(candidatos: list[GeocodeCandidato]) -> GeocodeCandidato | None:
    """Único candidato y preciso, o nada: un ROOFTOP/RANGE_INTERPOLATED sin
    partial_match, o una intersección exacta (GEOMETRIC_CENTER tipo
    `intersection` dio 0-300 m en el muestreo). Un candidato tipo `route` es el
    centro geométrico de la ruta — jamás se auto-elige."""
    if len(candidatos) != 1:
        return None
    unico = candidatos[0]
    if unico.partial_match or "route" in unico.tipos:
        return None
    if unico.location_type in _LOCATION_TYPES_PRECISOS or "intersection" in unico.tipos:
        return unico
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    rad = math.pi / 180.0
    d_lat = (lat2 - lat1) * rad
    d_lon = (lon2 - lon1) * rad
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(d_lon / 2) ** 2
    )
    return _RADIO_TIERRA_KM * 2 * math.asin(math.sqrt(a))


def es_pin_sospechoso(discrepancia_km: float) -> bool:
    return discrepancia_km > UMBRAL_PIN_SOSPECHOSO_KM
