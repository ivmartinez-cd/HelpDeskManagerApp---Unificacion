"""Resolución del username de operador de Gestión al nombre del catálogo.

Los eventos de facturación de ajax-by-rango traen el operador como username
(`vipaez`, `mjvela`), pero el catálogo scrapeado de /planificacion/ver solo
tiene nombres completos ("Victor Paez"). Gestión no expone la relación
username→persona, así que se infiere por convención de armado del username;
ante ambigüedad se prefiere no adivinar (el username queda como nombre).
"""

import unicodedata
from collections.abc import Callable

from src.modules.contadores.domain.entities.operador import Operador


def _normalize(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.lower().split())


def _match_nombre_completo(target: str, tokens: list[str]) -> bool:
    return target in (" ".join(tokens), "".join(tokens))


def _match_iniciales_mas_apellido(target: str, tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    return target == "".join(t[0] for t in tokens[:-1]) + tokens[-1]


def _match_prefijo_mas_apellido(target: str, tokens: list[str]) -> bool:
    if len(tokens) < 2 or not target.endswith(tokens[-1]):
        return False
    prefijo = target[: -len(tokens[-1])]
    return bool(prefijo) and tokens[0].startswith(prefijo)


def _match_palabra_suelta(target: str, tokens: list[str]) -> bool:
    return target in tokens


_MATCHERS: tuple[Callable[[str, list[str]], bool], ...] = (
    _match_nombre_completo,
    _match_iniciales_mas_apellido,
    _match_prefijo_mas_apellido,
    _match_palabra_suelta,
)


def resolve_nombre_operador(username: str, catalogo: list[Operador]) -> str | None:
    """Devuelve el nombre de catálogo que corresponde al username, o None si
    no hay match único (mejor mostrar el username que adjudicar eventos a la
    persona equivocada)."""
    target = _normalize(username)
    if not target:
        return None
    for matcher in _MATCHERS:
        candidatos = [op for op in catalogo if matcher(target, _normalize(op.nombre).split())]
        if len(candidatos) == 1:
            return candidatos[0].nombre
        if candidatos:
            return None
    return None
