"""Comparación normalizada de nombres de empresa entre SDS y Canal Directo.

Fiel al legacy offline_devices.py — los alias son datos de producción relevados manualmente;
agregar uno nuevo requiere también correr scripts/reclassify_offline_devices.py sobre los
equipos ya verificados, para no gastar SOAP de nuevo.
"""

import re
import unicodedata

_LEGAL_SUFFIX_RE = re.compile(
    r"\b(sa|saic|srl|sac|sacei|sapem|spa|group|grupo|ltd|ltda|inc|corp|co)\b\.?",
    re.IGNORECASE,
)
_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s]")
_WHITESPACE_RE = re.compile(r"\s+")

# Apodos, marcas y nombres de sitio/razón social que no comparten texto con el nombre de SDS.
# Un alias de una sola palabra solo matchea como token exacto (evita falsos positivos como
# "meli" dentro de otra palabra); uno de varias palabras matchea como substring de la frase.
# Clave: alias normalizado → nombre canónico (también normalizado).
_KNOWN_ALIASES: dict[str, str] = {
    "ausol": "autopistas del sol",
    "meli": "mercado libre",
    # AuSol y GCO comparten instancia de SDS — "el mismo cliente" a estos efectos.
    # La clave va sin "grupo" porque _LEGAL_SUFFIX_RE lo saca antes de que llegue acá.
    "gco": "autopistas del sol",
    "concesionario del oeste": "autopistas del sol",
    # Arcadium Lithium agrupa en SDS sitios/razones sociales que en Canal Directo figuran
    # con su propio nombre de planta/mina.
    "sal de vida": "arcadium lithium",
    "minera del altiplano": "arcadium lithium",
    "sales de jujuy": "arcadium lithium",
    # PSM es el nombre corto de Enap Sipetrol - YPF en SDS.
    "enap sipetrol ypf": "psm",
}


def normalize_company_name(name: str) -> str:
    """Sin acentos, sin mayúsculas, sin puntuación ni razón social, espacios colapsados."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    no_suffix = _LEGAL_SUFFIX_RE.sub(" ", ascii_name.lower())
    no_punct = _NON_ALNUM_RE.sub(" ", no_suffix)
    return _WHITESPACE_RE.sub(" ", no_punct).strip()


def expand_alias(normalized_name: str) -> str:
    """Reemplaza apodos conocidos por su forma canónica (alias de una palabra: token exacto;
    de varias palabras: primera ocurrencia como substring)."""
    if normalized_name in _KNOWN_ALIASES:
        return _KNOWN_ALIASES[normalized_name]
    tokens = normalized_name.split()
    for alias, canonical in _KNOWN_ALIASES.items():
        if " " in alias:
            if alias in normalized_name:
                return normalized_name.replace(alias, canonical)
        elif alias in tokens:
            return normalized_name.replace(alias, canonical)
    return normalized_name


def same_company(a: str, b: str) -> bool:
    """True si a y b son razonablemente el mismo cliente: match exacto o contención en
    cualquier dirección, tras normalizar y expandir alias en ambos lados."""
    na, nb = normalize_company_name(a), normalize_company_name(b)
    if not na or not nb:
        return False
    na, nb = expand_alias(na), expand_alias(nb)
    return na == nb or na in nb or nb in na
