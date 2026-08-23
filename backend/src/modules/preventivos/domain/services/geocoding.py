"""Armado de dirección y elección de candidato de geocode — dominio puro, sin
llamadas a Google. Misma heurística que
`liquidaciones/domain/services/geolocalizacion.py` (calibrada ahí con
muestreo real 2026-08-15, n=20: geocode urbano argentino con mediana 22 m de
error; "Ruta X KM Y" devuelve el centro de toda la ruta, 5-330 km de error).
Duplicada a propósito: son funciones puras sin estado ni costo compartido —
extraerlas a shared por tres líneas hubiera sido la abstracción prematura que
la guía pide evitar; lo caro (el gateway HTTP y el cache) sí está en shared."""

import re

from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato

# Los domicilios de Siges arrastran sufijos de formulario vacíos ("Piso: Dpto:",
# "Piso:7 Dpto:") y un " 0" final de altura sin dato — ruido para el geocoder.
_SUFIJO_PISO = re.compile(r"\s*Piso\s*:.*$", re.IGNORECASE)
_ALTURA_CERO = re.compile(r"\s+0$")

_LOCATION_TYPES_PRECISOS = ("ROOFTOP", "RANGE_INTERPOLATED")


def normalizar_domicilio(domicilio: str) -> str:
    limpio = _SUFIJO_PISO.sub("", domicilio).strip()
    limpio = _ALTURA_CERO.sub("", limpio).strip(" ,")
    return "" if limpio == "0" else limpio


def armar_direccion(domicilio: str, ciudad: str, provincia: str) -> str | None:
    """Query de geocode `domicilio, ciudad, provincia, Argentina`. `None` si
    no hay domicilio (no tiene sentido geocodificar solo la ciudad)."""
    dom_norm = normalizar_domicilio(domicilio)
    if not dom_norm:
        return None
    partes = [dom_norm]
    if ciudad.strip():
        partes.append(ciudad.strip())
    if provincia.strip():
        partes.append(provincia.strip())
    partes.append("Argentina")
    return ", ".join(partes)


def elegir_automatico(candidatos: list[GeocodeCandidato]) -> GeocodeCandidato | None:
    """Único candidato y preciso, o nada: un ROOFTOP/RANGE_INTERPOLATED sin
    partial_match, o una intersección exacta. Un candidato tipo `route` es el
    centro geométrico de la ruta — jamás se auto-elige."""
    if len(candidatos) != 1:
        return None
    unico = candidatos[0]
    if unico.partial_match or "route" in unico.tipos:
        return None
    if unico.location_type in _LOCATION_TYPES_PRECISOS or "intersection" in unico.tipos:
        return unico
    return None
