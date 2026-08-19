"""Tier 1 de geovalidación (Fase 2): comparación pura entre la provincia
declarada en Siges (`DesProvincia`) y la provincia real que devuelve el
reverse de Georef para el pin. La llamada de red vive en application/
infrastructure — esto es dominio puro, sin I/O, con tests directos."""

import unicodedata

# Alias reales de nombre de provincia entre Siges y Georef — CABA es el único
# confirmado hasta ahora (Siges suele guardar "Capital Federal"/"CABA", Georef
# siempre devuelve "Ciudad Autónoma de Buenos Aires"). Agregar acá solo con
# evidencia real de un caso, no especulativamente.
_ALIAS_PROVINCIA: dict[str, str] = {
    "caba": "ciudad autonoma de buenos aires",
    "capital federal": "ciudad autonoma de buenos aires",
}


def _normalizar_provincia(nombre: str) -> str:
    sin_acentos = "".join(
        ch for ch in unicodedata.normalize("NFD", nombre) if not unicodedata.combining(ch)
    )
    limpio = sin_acentos.strip().lower()
    return _ALIAS_PROVINCIA.get(limpio, limpio)


def provincias_compatibles(declarada: str | None, real: str) -> bool:
    """`declarada` es `DesProvincia` de Siges (puede venir vacío — LEFT JOIN
    con `Ciudad`, muchas sucursales no la tienen cargada); `real` es la
    provincia que devolvió el reverse de Georef para el pin."""
    if not declarada or not declarada.strip():
        return True  # sin dato declarado, no hay nada que contradecir
    return _normalizar_provincia(declarada) == _normalizar_provincia(real)
