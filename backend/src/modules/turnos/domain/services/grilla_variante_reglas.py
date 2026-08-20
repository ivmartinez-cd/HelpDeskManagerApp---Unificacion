"""Reglas puras de una grilla variante (modo vacaciones, ADR-025): vigencia,
consistencia de franjas y advertencias de cobertura. Sin I/O: los casos de
uso cargan los datos y llaman acá."""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, time
from typing import Literal

from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante, VarianteSlot
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import (
    InvalidVarianteRangeError,
    VarianteFranjaInvalidaError,
    VarianteFranjasSolapadasError,
    VarianteOperadorSolapadoError,
    VarianteSinFranjasError,
)

TipoAdvertencia = Literal["HUECO", "SIN_OPERADOR", "OPERADOR_AUSENTE"]


@dataclass(frozen=True, slots=True)
class AdvertenciaCobertura:
    """No bloquea el guardado: un hueco puede ser deliberado (INSUMOS sin
    nadie 8:00-8:30 en el caso real). `casilla_id`/`dia_semana`/horas aplican
    a HUECO y SIN_OPERADOR; `user_id`/`desde`/`hasta` a OPERADOR_AUSENTE."""

    tipo: TipoAdvertencia
    casilla_id: uuid.UUID | None = None
    dia_semana: int | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    user_id: uuid.UUID | None = None
    desde: date | None = None
    hasta: date | None = None


Intervalo = tuple[time, time]


def validar_vigencia(desde: date, hasta: date) -> None:
    if desde > hasta:
        raise InvalidVarianteRangeError()


def hay_solapamiento_vigencia(
    desde: date, hasta: date, existentes: Iterable[GrillaVariante]
) -> bool:
    """Una sola variante ACTIVA vigente por fecha (ADR-025)."""
    return any(
        v.estado == "ACTIVA" and not (v.desde > hasta or desde > v.hasta) for v in existentes
    )


def validar_franjas(slots: list[VarianteSlot]) -> None:
    if not slots:
        raise VarianteSinFranjasError()
    for s in slots:
        if s.hora_inicio >= s.hora_fin:
            raise VarianteFranjaInvalidaError(
                f"{_hhmm(s.hora_inicio)}-{_hhmm(s.hora_fin)} (inicio debe ser menor que fin)"
            )
        if not 0 <= s.dia_semana <= 6:
            raise VarianteFranjaInvalidaError(f"día de semana {s.dia_semana} fuera de 0..6")
    _validar_sin_solape_por_casilla(slots)
    _validar_operador_sin_solape(slots)


def _validar_sin_solape_por_casilla(slots: list[VarianteSlot]) -> None:
    por_grupo: dict[tuple[uuid.UUID, int], list[VarianteSlot]] = {}
    for s in slots:
        por_grupo.setdefault((s.casilla_id, s.dia_semana), []).append(s)
    for grupo in por_grupo.values():
        ordenadas = sorted(grupo, key=lambda s: s.hora_inicio)
        for anterior, actual in zip(ordenadas, ordenadas[1:], strict=False):
            if actual.hora_inicio < anterior.hora_fin:
                raise VarianteFranjasSolapadasError(
                    f"{_rango(anterior)} y {_rango(actual)} (día {actual.dia_semana})"
                )


def _validar_operador_sin_solape(slots: list[VarianteSlot]) -> None:
    por_user_dia: dict[tuple[uuid.UUID, int], list[VarianteSlot]] = {}
    for s in slots:
        for user_id in s.user_ids:
            por_user_dia.setdefault((user_id, s.dia_semana), []).append(s)
    for (user_id, dia), franjas in por_user_dia.items():
        ordenadas = sorted(franjas, key=lambda s: s.hora_inicio)
        for anterior, actual in zip(ordenadas, ordenadas[1:], strict=False):
            if actual.hora_inicio < anterior.hora_fin:
                raise VarianteOperadorSolapadoError(
                    f"operador {user_id} en {_rango(anterior)} y {_rango(actual)} (día {dia})"
                )


def advertencias_de_cobertura(
    variante_slots: list[VarianteSlot], titular_slots: list[Slot]
) -> list[AdvertenciaCobertura]:
    """HUECO = tramo que la titular cubre en esa casilla+día y la variante no;
    SIN_OPERADOR = franja de la variante sin nadie asignado."""
    advertencias = [
        AdvertenciaCobertura(
            tipo="SIN_OPERADOR",
            casilla_id=s.casilla_id,
            dia_semana=s.dia_semana,
            hora_inicio=s.hora_inicio,
            hora_fin=s.hora_fin,
        )
        for s in variante_slots
        if not s.user_ids
    ]
    advertencias += _huecos(variante_slots, titular_slots)
    return advertencias


def _huecos(
    variante_slots: list[VarianteSlot], titular_slots: list[Slot]
) -> list[AdvertenciaCobertura]:
    titular = _agrupar(titular_slots)
    variante = _agrupar(variante_slots)
    huecos: list[AdvertenciaCobertura] = []
    for (casilla_id, dia), intervalos in sorted(titular.items(), key=_orden_grupo):
        cubierto = _unir(variante.get((casilla_id, dia), []))
        huecos += [
            AdvertenciaCobertura(
                tipo="HUECO",
                casilla_id=casilla_id,
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
            )
            for inicio, fin in _restar(_unir(intervalos), cubierto)
        ]
    return huecos


def _orden_grupo(item: tuple[tuple[uuid.UUID, int], list[Intervalo]]) -> tuple[str, int]:
    (casilla_id, dia), _ = item
    return (str(casilla_id), dia)


def _agrupar(
    franjas: Iterable[VarianteSlot | Slot],
) -> dict[tuple[uuid.UUID, int], list[Intervalo]]:
    grupos: dict[tuple[uuid.UUID, int], list[Intervalo]] = {}
    for f in franjas:
        grupos.setdefault((f.casilla_id, f.dia_semana), []).append((f.hora_inicio, f.hora_fin))
    return grupos


def _unir(intervalos: list[Intervalo]) -> list[Intervalo]:
    unidos: list[Intervalo] = []
    for inicio, fin in sorted(intervalos):
        if unidos and inicio <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((inicio, fin))
    return unidos


def _restar(base: list[Intervalo], quitar: list[Intervalo]) -> list[Intervalo]:
    """`base` menos `quitar`, ambos ya unidos y ordenados."""
    resultado: list[Intervalo] = []
    for inicio, fin in base:
        cursor = inicio
        for q_inicio, q_fin in quitar:
            if q_fin <= cursor or q_inicio >= fin:
                continue
            if q_inicio > cursor:
                resultado.append((cursor, q_inicio))
            cursor = max(cursor, q_fin)
        if cursor < fin:
            resultado.append((cursor, fin))
    return resultado


def _hhmm(t: time) -> str:
    return t.strftime("%H:%M")


def _rango(s: VarianteSlot) -> str:
    return f"{_hhmm(s.hora_inicio)}-{_hhmm(s.hora_fin)}"
