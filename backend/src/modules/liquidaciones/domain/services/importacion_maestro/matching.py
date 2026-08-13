"""Matching de nombre de SPST contra los nombres ya resueltos — puro, solo strings,
sin tocar entidades ni repositorios (el use case es quien mapea el nombre matcheado
a un `Spst.id` real)."""

from collections.abc import Sequence


def matchear_spst(nombre_buscado: str | None, nombres_disponibles: Sequence[str]) -> str | None:
    """Exacto (case-insensitive) primero; si no matchea, substring en ambas
    direcciones (mismo criterio que el legacy) — devuelve el nombre tal como
    aparece en `nombres_disponibles`, no el buscado."""
    if not nombre_buscado:
        return None
    buscado = nombre_buscado.strip().lower()
    for nombre in nombres_disponibles:
        if nombre.strip().lower() == buscado:
            return nombre
    for nombre in nombres_disponibles:
        normalizado = nombre.strip().lower()
        if buscado in normalizado or normalizado in buscado:
            return nombre
    return None
