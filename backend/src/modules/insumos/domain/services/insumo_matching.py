"""Heurística de selección de insumo dentro de una familia de Canal Directo.

Portada de `insumo_matching.select_insumo_id` del legacy sin cambios de comportamiento
(los tests de caracterización son los mismos casos reales). El caller es responsable de
resolver `options` a la forma normalizada `{insumo_id: nombre_o_dict}` — el SOAP
getArticleParts devuelve [{"id","name"}] y se normaliza en infraestructura.

Nota: en producción ninguna vía trae `sku` en las opciones (verificado contra el servicio
real) — el paso 1 (match exacto por SKU) queda para el día que Canal Directo cargue SKUs
en la familia, pero hoy nunca dispara. No eliminarlo como dead code: es forward-compatible.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

from src.modules.insumos.domain.errors import (
    FamiliaSinInsumosError,
    InsumoAmbiguoError,
    InsumoNoConfiguradoError,
)

logger = logging.getLogger(__name__)

InsumoOptions = Mapping[str, str | Mapping[str, str]]

# Palabras de color en inglés (nombres de opciones de CD) → equivalentes en español/inglés
# que pueden aparecer en la descripción del consumible de Insight. El match busca cualquier
# palabra del grupo en el NOMBRE de la opción (no solo la clave en inglés): hay ítems
# cargados en español (ej. familia 203, "Developer ... - Negro" en vez de "- Black").
_COLOR_KEYWORDS: tuple[tuple[str, ...], ...] = (
    ("black", "negro"),
    ("cyan", "cian", "celeste"),
    ("yellow", "amarillo"),
    ("magenta",),
)

# Drum y Developer son tipos DISTINTOS en CD: no mezclarlos.
_DRUM_OPT = ("drum",)
_DEVELOPER_OPT = ("developer", "revelador")
_WASTE_OPT = ("waste", "collection")
_STAPLE_OPT = ("staple",)
_ALL_NON_TONER = (*_DRUM_OPT, *_DEVELOPER_OPT, *_WASTE_OPT, *_STAPLE_OPT)

_NON_BLACK_COLOR_WORDS = ("cyan", "cian", "magenta", "yellow", "amarillo", "celeste")

_WASTE_DESC_WORDS = (
    "waste", "residuo", "container", "recogida", "collection unit", "toner collection"
)

# Centinela del tipo "toner": se filtra por exclusión (todo lo que NO es drum/developer/
# waste/staples), no por keywords propias.
_TONER: tuple[str, ...] = ()

# Etiquetas legibles para InsumoNoConfiguradoError — identidad de tupla, no igualdad
# (mismo motivo que la comparación `type_keywords is _TONER` de _filter_by_type).
_TYPE_LABELS: dict[int, str] = {
    id(_WASTE_OPT): "waste/tolva de desecho",
    id(_STAPLE_OPT): "staples/grapas",
    id(_DEVELOPER_OPT): "developer/revelador",
    id(_DRUM_OPT): "drum/tambor",
    id(_TONER): "toner/cartucho",
}


@dataclass(frozen=True)
class InsumoQuery:
    """Contexto de la selección: el consumible solicitado por Insight y la familia de CD."""

    familia_name: str
    device_serial: str
    requested_sku: str = ""
    description: str = ""
    override_insumo_id: str | None = None


def select_insumo_id(options: InsumoOptions, query: InsumoQuery) -> str:
    """Encuentra el insumo de la familia que coincide con el consumible solicitado.

    Estrategia en orden de confianza:
    0. override_insumo_id informado (el operador ya desambiguó a mano) → se usa directo.
    1. Match exacto por SKU (si CD tiene SKUs configurados en la familia).
    2. Match por tipo (drum/developer/waste/staples/toner) + color, solo con candidato único.
    3. Única opción disponible: se toma sin validar.
    4. Múltiples opciones sin match único → InsumoAmbiguoError con las opciones candidatas.
    """
    if query.override_insumo_id:
        _log_selection(query, query.override_insumo_id, "forzado por override_insumo_id")
        return query.override_insumo_id
    if not options:
        raise FamiliaSinInsumosError(query.familia_name, query.device_serial)

    by_sku = _match_by_sku(options, query)
    if by_sku is not None:
        return by_sku

    if query.description and len(options) > 1:
        by_type_and_color = _match_by_type_and_color(options, query)
        if by_type_and_color is not None:
            return by_type_and_color

    if len(options) == 1:
        only_option = next(iter(options))
        _log_selection(query, only_option, "única opción disponible")
        return only_option

    raise InsumoAmbiguoError(
        f"Familia '{query.familia_name}' (serie {query.device_serial}) tiene múltiples "
        f"insumos y no se pudo determinar cuál usar automáticamente "
        f"(SKU='{query.requested_sku}', desc='{query.description}').",
        options=_insumo_options(options),
    )


def _match_by_sku(options: InsumoOptions, query: InsumoQuery) -> str | None:
    requested_sku = str(query.requested_sku).strip()
    if not requested_sku:
        return None
    for insumo_id, insumo_info in options.items():
        insumo_dict = insumo_info if isinstance(insumo_info, Mapping) else {}
        insumo_sku = str(insumo_dict.get("sku", "")).strip()
        if insumo_sku and insumo_sku == requested_sku:
            _log_selection(query, insumo_id, f"seleccionado por SKU {requested_sku}")
            return insumo_id
    return None


def _match_by_type_and_color(options: InsumoOptions, query: InsumoQuery) -> str | None:
    """Filtra por tipo de consumible y después por color dentro del tipo.

    El filtro de tipo evita que un "Imaging Unit" se resuelva como toner por el color
    que comparten en el nombre. Si el color sigue ambiguo dentro del tipo, se lanza
    InsumoAmbiguoError con los candidatos (caso real: solicitud 970568, dos Cyan de
    distinta capacidad).

    Caso aparte: si la descripción identifica un tipo y la familia no tiene NINGÚN
    insumo de ese tipo, no es ambigüedad → InsumoNoConfiguradoError (falta cargar el
    insumo en el catálogo de Canal Directo, no hay nada válido para elegir).
    """
    desc_lower = query.description.lower()
    type_keywords = _type_keywords_for_description(desc_lower)
    candidates = _filter_by_type(options, type_keywords)

    if type_keywords is not None and not candidates:
        raise InsumoNoConfiguradoError(
            f"Familia '{query.familia_name}' (serie {query.device_serial}) no tiene "
            f"ningún insumo de tipo {_TYPE_LABELS[id(type_keywords)]} configurado en "
            f"Canal Directo (SKU='{query.requested_sku}', desc='{query.description}'). "
            "Falta cargar ese insumo en el catálogo de la familia en Canal Directo — no "
            "es un problema de matching.",
            options=_insumo_options(options),
        )

    if len(candidates) == 1:
        chosen = next(iter(candidates))
        _log_selection(query, chosen, f"seleccionado por tipo (desc={query.description!r})")
        return chosen

    color_matches = _match_colors(options, candidates, desc_lower)
    if len(color_matches) == 1:
        _log_selection(
            query, color_matches[0], f"seleccionado por color+tipo (desc={query.description!r})"
        )
        return color_matches[0]
    if len(color_matches) > 1:
        raise InsumoAmbiguoError(
            f"Familia '{query.familia_name}' (serie {query.device_serial}) tiene múltiples "
            f"insumos candidatos para el mismo color (SKU='{query.requested_sku}', "
            f"desc='{query.description}').",
            options=_insumo_options(options, color_matches),
        )
    return None


def _filter_by_type(
    options: InsumoOptions, type_keywords: tuple[str, ...] | None
) -> InsumoOptions:
    """Candidatos del tipo que indica la descripción de Insight (sin filtrar si no es claro)."""
    if type_keywords is None:
        return options
    if type_keywords is _TONER:
        return {
            k: v
            for k, v in options.items()
            if not any(kw in _opt_name(options, k) for kw in _ALL_NON_TONER)
        }
    return {
        k: v
        for k, v in options.items()
        if any(kw in _opt_name(options, k) for kw in type_keywords)
    }


def _type_keywords_for_description(desc_lower: str) -> tuple[str, ...] | None:
    """Keywords del tipo de consumible según la descripción, o None si no es identificable.

    "tambor"/"imaging unit" → drum; "developer" explícito (sin señal de drum) → developer;
    "unidad de recogida"/"collection unit" → waste; "staple"/"grapa" → staples;
    "cartucho"/"toner"/"cartridge" → toner (por exclusión).
    """
    is_drum = any(kw in desc_lower for kw in ("drum", "tambor", "imaging unit", "unidad de imagen"))
    if any(kw in desc_lower for kw in _WASTE_DESC_WORDS):
        return _WASTE_OPT
    if any(kw in desc_lower for kw in ("staple", "grapa")):
        return _STAPLE_OPT
    if "developer" in desc_lower and not is_drum:
        return _DEVELOPER_OPT
    if is_drum:
        return _DRUM_OPT
    if any(kw in desc_lower for kw in ("cartucho", "toner", "cartridge")):
        return _TONER
    return None


def _match_colors(
    options: InsumoOptions, candidates: InsumoOptions, desc_lower: str
) -> list[str]:
    matches: list[str] = []
    for insumo_id in candidates:
        opt_name = _opt_name(options, insumo_id)
        for keywords in _COLOR_KEYWORDS:
            if any(kw in opt_name for kw in keywords) and any(kw in desc_lower for kw in keywords):
                matches.append(insumo_id)
                break
    if not matches:
        return _cmy_fallback(options, candidates, desc_lower)
    return matches


def _cmy_fallback(
    options: InsumoOptions, candidates: InsumoOptions, desc_lower: str
) -> list[str]:
    """Algunos drums HP cubren C+M+Y en una sola unidad llamada "CMY": si la descripción
    pide un color no-negro y no hubo match directo, buscar la opción CMY única."""
    if not any(kw in desc_lower for kw in _NON_BLACK_COLOR_WORDS):
        return []
    cmy_options = [oid for oid in candidates if "cmy" in _opt_name(options, oid)]
    return cmy_options if len(cmy_options) == 1 else []


def _opt_name(options: InsumoOptions, insumo_id: str) -> str:
    value = options[insumo_id]
    name = value if isinstance(value, str) else str(value.get("nombre", ""))
    return name.lower()


def _insumo_options(
    options: InsumoOptions, candidate_ids: list[str] | None = None
) -> list[dict[str, str]]:
    """Formatea las opciones de getArticleParts como [{"id", "name"}] para el frontend."""
    ids = candidate_ids if candidate_ids is not None else list(options)
    result: list[dict[str, str]] = []
    for oid in ids:
        value = options[oid]
        name = value if isinstance(value, str) else str(value.get("nombre", value))
        result.append({"id": oid, "name": name})
    return result


def _log_selection(query: InsumoQuery, insumo_id: str, how: str) -> None:
    logger.info(
        "Familia '%s' (serie %s): insumo %s %s (SKU=%s)",
        query.familia_name,
        query.device_serial,
        insumo_id,
        how,
        query.requested_sku,
    )
