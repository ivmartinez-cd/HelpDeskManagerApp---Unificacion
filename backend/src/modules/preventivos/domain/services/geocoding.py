"""Armado de dirección y elección de candidato de geocode — dominio puro, sin
llamadas a Google. Misma heurística que
`liquidaciones/domain/services/geolocalizacion.py` (calibrada ahí con
muestreo real 2026-08-15, n=20: geocode urbano argentino con mediana 22 m de
error; "Ruta X KM Y" devuelve el centro de toda la ruta, 5-330 km de error).
Duplicada a propósito: son funciones puras sin estado ni costo compartido —
extraerlas a shared por tres líneas hubiera sido la abstracción prematura que
la guía pide evitar; lo caro (el gateway HTTP y el cache) sí está en shared."""

import re
import statistics
import unicodedata

from src.modules.preventivos.domain.services.coordenadas import haversine_km
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
# validaba localidad, solo precisión/unicidad — de ahí este chequeo de texto.
_CABA_ALIASES = frozenset({"caba", "ciudad autonoma de buenos aires", "capital federal"})
_CABA_EN_RESULTADO = "autonoma de buenos aires"

# Barrido 2026-08-23 (McDonald's Entre Ríos y Caseros → San Justo, Dia
# Belgrano 664 Garín → Lomas de Zamora, KFC J.M.de Rosas San Justo → San
# Martín, Dia Argerich Hurlingham → CABA, Tasa Panamericana Km57,5 Escobar →
# Don Torcuato, Celsur Av. Gral. Perón Benavídez → Lanús): el chequeo de
# CABA por texto no generaliza — un mismo nombre de calle/avenida se repite
# en partidos distintos del Conurbano, y ni el `formatted_address` de Google
# es confiable como filtro (el caso Garín devolvía "B1619 Garín" en el
# `formatted_address` estando igual a 35km, porque ese código postal cubre
# una zona amplia). En cambio, un chequeo geométrico contra otras sucursales
# YA confiables de la misma (ciudad, provincia) sí detectó los 6 casos de
# ese barrido. CABA se excluye de este chequeo (ver
# `agrupar_referencias_por_ciudad`): sigue resuelta por el chequeo de texto
# de arriba.
_MIN_REFERENCIAS = 5
_UMBRAL_REFERENCIAS_KM = 2.0


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


def clave_ubicacion(ciudad: str, provincia: str) -> tuple[str, str]:
    """Clave normalizada (ciudad, provincia) para agrupar/consultar
    referencias geográficas — misma normalización que usa `elegir_automatico`
    para el chequeo de CABA."""
    return (_normalizar(ciudad), _normalizar(provincia))


def agrupar_referencias_por_ciudad(
    entradas: list[tuple[str, str, float, float]],
) -> dict[tuple[str, str], list[tuple[float, float]]]:
    """Agrupa (ciudad, provincia, lat, lon) de sucursales ya confiables
    (override vigente o raw de Siges válido) por `clave_ubicacion`, para
    alimentar el chequeo geométrico de `elegir_automatico`. CABA se excluye
    a propósito: es geográficamente demasiado grande/diversa para que un
    solo centroide tenga sentido — probado en la auditoría 2026-08-23 con
    dos casos correctos (Felfort, Finadiet) que aparecían como falso
    positivo en el extremo débil de la lista; ahí sigue rigiendo el chequeo
    de texto de CABA."""
    agrupadas: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for ciudad, provincia, lat, lon in entradas:
        clave = clave_ubicacion(ciudad, provincia)
        if clave[0] in _CABA_ALIASES:
            continue
        agrupadas.setdefault(clave, []).append((lat, lon))
    return agrupadas


def _consistente_con_referencias(
    lat: float, lon: float, referencias: tuple[tuple[float, float], ...]
) -> bool:
    if len(referencias) < _MIN_REFERENCIAS:
        return True
    lat_mediana = statistics.median(p[0] for p in referencias)
    lon_mediana = statistics.median(p[1] for p in referencias)
    return haversine_km(lat, lon, lat_mediana, lon_mediana) <= _UMBRAL_REFERENCIAS_KM


def _localidad_consistente(
    ciudad: str, unico: GeocodeCandidato, referencias: tuple[tuple[float, float], ...]
) -> bool:
    if _normalizar(ciudad) in _CABA_ALIASES:
        return _CABA_EN_RESULTADO in _normalizar(unico.formatted_address)
    return _consistente_con_referencias(unico.latitud, unico.longitud, referencias)


def elegir_automatico(
    candidatos: list[GeocodeCandidato],
    ciudad: str = "",
    referencias: tuple[tuple[float, float], ...] = (),
) -> GeocodeCandidato | None:
    """Único candidato y preciso, o nada. CABA se valida por texto; el resto
    de las ciudades, por geometría contra `referencias` si hay suficientes —
    ver notas de las auditorías arriba."""
    if len(candidatos) != 1:
        return None
    unico = candidatos[0]
    if unico.partial_match or "route" in unico.tipos:
        return None
    if not _localidad_consistente(ciudad, unico, referencias):
        return None
    if unico.location_type in _LOCATION_TYPES_PRECISOS or "intersection" in unico.tipos:
        return unico
    return None
