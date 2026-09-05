"""Reglas puras comunes a toda franja horaria de turnos -- titular
(`Slot`) o de una grilla variante (`VarianteSlot`): horario consistente, día
de semana en 0..6 y sin superposición dentro de la misma casilla y día. Cada
caller traduce el detalle a su propio error de dominio."""

import uuid
from collections.abc import Iterable
from datetime import time
from typing import Protocol

from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import FranjaInvalidaError, FranjasSolapadasError


class Franja(Protocol):
    casilla_id: uuid.UUID
    dia_semana: int
    hora_inicio: time
    hora_fin: time


def detalle_franja_invalida(franja: Franja) -> str | None:
    """`None` si la franja es consistente; si no, el motivo legible."""
    if franja.hora_inicio >= franja.hora_fin:
        return f"{rango(franja)} (inicio debe ser menor que fin)"
    if not 0 <= franja.dia_semana <= 6:
        return f"día de semana {franja.dia_semana} fuera de 0..6"
    return None


def detalle_solape_por_casilla[F: Franja](franjas: Iterable[F]) -> str | None:
    """Primer par de franjas de la misma casilla y día que se superponen, o
    `None`. Tocarse en el borde (fin == inicio de la siguiente) no es solape."""
    por_grupo: dict[tuple[uuid.UUID, int], list[F]] = {}
    for f in franjas:
        por_grupo.setdefault((f.casilla_id, f.dia_semana), []).append(f)
    for grupo in por_grupo.values():
        ordenadas = sorted(grupo, key=lambda f: f.hora_inicio)
        for anterior, actual in zip(ordenadas, ordenadas[1:], strict=False):
            if actual.hora_inicio < anterior.hora_fin:
                return f"{rango(anterior)} y {rango(actual)} (día {actual.dia_semana})"
    return None


def validar_franja_titular(slot: Slot, existentes: Iterable[Slot]) -> None:
    """Invariantes de una franja de la grilla titular al crearla o editarla.
    `existentes` = las demás franjas de la misma casilla (la propia, si está,
    se excluye por id)."""
    detalle = detalle_franja_invalida(slot)
    if detalle is not None:
        raise FranjaInvalidaError(detalle)
    otras = [s for s in existentes if s.id != slot.id]
    solape = detalle_solape_por_casilla([*otras, slot])
    if solape is not None:
        raise FranjasSolapadasError(solape)


def hhmm(t: time) -> str:
    return t.strftime("%H:%M")


def rango(f: Franja) -> str:
    return f"{hhmm(f.hora_inicio)}-{hhmm(f.hora_fin)}"
