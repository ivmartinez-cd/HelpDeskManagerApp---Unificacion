"""Regla de visibilidad de zonas: el alcance del módulo son las cuadrículas
de despacho con técnicos locales; INTERIOR (PSTs), agrupaciones de PST
(BSAS.*, CBA..*, ...) y valores basura quedan fuera. No hay una regla de
datos en Siges que distinga local de interior (632 sucursales de INTERIOR
también tienen prestador CD - ver exploración ronda 4), así que la exclusión
es una lista configurable de patrones — data-driven para lo que importa: una
zona local nueva (p. ej. NORTE5) aparece sola sin tocar código ni config."""

from collections.abc import Sequence


def zona_excluida(zona: str, patrones_exclusion: Sequence[str]) -> bool:
    """`"X*"` excluye por prefijo; cualquier otro patrón es igualdad exacta.
    Comparación normalizada (trim + mayúsculas). Una zona vacía siempre está
    excluida — es basura de carga, no una zona."""
    valor = zona.strip().upper()
    if not valor:
        return True
    for patron in patrones_exclusion:
        p = patron.strip().upper()
        if not p:
            continue
        if p.endswith("*"):
            if valor.startswith(p[:-1]):
                return True
        elif valor == p:
            return True
    return False
