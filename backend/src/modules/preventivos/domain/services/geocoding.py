"""Armado de dirección y elección de candidato de geocode — dominio puro, sin
llamadas a Google. Misma heurística que
`liquidaciones/domain/services/geolocalizacion.py` (calibrada ahí con
muestreo real 2026-08-15, n=20: geocode urbano argentino con mediana 22 m de
error; "Ruta X KM Y" devuelve el centro de toda la ruta, 5-330 km de error).
Duplicada a propósito: son funciones puras sin estado ni costo compartido —
extraerlas a shared por tres líneas hubiera sido la abstracción prematura que
la guía pide evitar; lo caro (el gateway HTTP y el cache) sí está en shared."""

import re
import unicodedata

from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato

# Los domicilios de Siges arrastran sufijos de formulario vacíos ("Piso: Dpto:",
# "Piso:7 Dpto:") y un " 0" final de altura sin dato — ruido para el geocoder.
_SUFIJO_PISO = re.compile(r"\s*Piso\s*:.*$", re.IGNORECASE)
_ALTURA_CERO = re.compile(r"\s+0$")

_LOCATION_TYPES_PRECISOS = ("ROOFTOP", "RANGE_INTERPOLATED")

# Auditoría 2026-08-23: muchas calles de CABA (Rivadavia, Chile, Chiclana,
# Juan B. Justo...) se repiten en el Conurbano. Cuando Google devuelve un
# único candidato para una sucursal con ciudad=CABA, a veces ese candidato
# cae en el partido equivocado en vez de en CABA — cross-check contra
# Nominatim confirmó 9 casos reales (Boedo, Monserrat, Nueva Pompeya,
# Almagro, Rivadavia 789, Juan B. Justo x2, Av. Mosconi, Chiclana 3345) donde
# la coordenada original de Siges era la correcta. `elegir_automatico` no
# validaba localidad, solo precisión/unicidad — de ahí este chequeo.
_CABA_ALIASES = frozenset({"caba", "ciudad autonoma de buenos aires", "capital federal"})
_CABA_EN_RESULTADO = "autonoma de buenos aires"


def _sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def _normalizar(texto: str) -> str:
    return _sin_acentos(texto).strip().lower()


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


def elegir_automatico(
    candidatos: list[GeocodeCandidato], ciudad: str = ""
) -> GeocodeCandidato | None:
    """Único candidato y preciso, o nada: un ROOFTOP/RANGE_INTERPOLATED sin
    partial_match, o una intersección exacta. Un candidato tipo `route` es el
    centro geométrico de la ruta — jamás se auto-elige. Si la sucursal es de
    CABA, el candidato tiene que caer efectivamente en CABA (no en un partido
    del Conurbano con la misma calle) — ver nota de la auditoría arriba."""
    if len(candidatos) != 1:
        return None
    unico = candidatos[0]
    if unico.partial_match or "route" in unico.tipos:
        return None
    if _normalizar(ciudad) in _CABA_ALIASES and _CABA_EN_RESULTADO not in _normalizar(
        unico.formatted_address
    ):
        return None
    if unico.location_type in _LOCATION_TYPES_PRECISOS or "intersection" in unico.tipos:
        return unico
    return None
