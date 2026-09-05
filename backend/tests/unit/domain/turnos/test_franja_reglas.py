"""Reglas comunes a franjas titulares y de grilla variante (`franja_reglas`)."""

import uuid
from datetime import time

import pytest

from src.modules.turnos.domain.entities.grilla_variante import VarianteSlot
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import FranjaInvalidaError, FranjasSolapadasError
from src.modules.turnos.domain.services.franja_reglas import (
    detalle_franja_invalida,
    detalle_solape_por_casilla,
    validar_franja_titular,
)

CASILLA = uuid.uuid4()


def _slot(inicio: time, fin: time, dia: int = 0, casilla: uuid.UUID = CASILLA) -> Slot:
    return Slot(
        id=uuid.uuid4(),
        casilla_id=casilla,
        hora_inicio=inicio,
        hora_fin=fin,
        dia_semana=dia,
        sort_order=0,
    )


def test_franja_consistente_no_tiene_detalle() -> None:
    assert detalle_franja_invalida(_slot(time(8), time(12))) is None


def test_inicio_mayor_o_igual_que_fin_es_invalida() -> None:
    assert detalle_franja_invalida(_slot(time(20), time(19))) == (
        "20:00-19:00 (inicio debe ser menor que fin)"
    )
    assert detalle_franja_invalida(_slot(time(8), time(8))) is not None


def test_dia_fuera_de_0_a_6_es_invalido() -> None:
    assert detalle_franja_invalida(_slot(time(8), time(9), dia=7)) == (
        "día de semana 7 fuera de 0..6"
    )
    assert detalle_franja_invalida(_slot(time(8), time(9), dia=-1)) is not None
    assert detalle_franja_invalida(_slot(time(8), time(9), dia=6)) is None


def test_solape_solo_dentro_de_la_misma_casilla_y_dia() -> None:
    base = _slot(time(8), time(12))

    assert detalle_solape_por_casilla([base, _slot(time(11), time(13))]) == (
        "08:00-12:00 y 11:00-13:00 (día 0)"
    )
    assert detalle_solape_por_casilla([base, _slot(time(12), time(13))]) is None  # borde
    assert detalle_solape_por_casilla([base, _slot(time(11), time(13), dia=1)]) is None
    assert (
        detalle_solape_por_casilla([base, _slot(time(11), time(13), casilla=uuid.uuid4())]) is None
    )


def test_las_reglas_sirven_tambien_para_franjas_de_variante() -> None:
    """`VarianteSlot` cumple el mismo protocolo: la grilla de vacaciones reutiliza
    estas reglas en vez de duplicarlas."""
    a = VarianteSlot(
        id=uuid.uuid4(),
        casilla_id=CASILLA,
        dia_semana=0,
        hora_inicio=time(8),
        hora_fin=time(12),
        sort_order=0,
    )
    b = VarianteSlot(
        id=uuid.uuid4(),
        casilla_id=CASILLA,
        dia_semana=0,
        hora_inicio=time(10),
        hora_fin=time(11),
        sort_order=1,
    )

    assert detalle_franja_invalida(a) is None
    assert detalle_solape_por_casilla([a, b]) == "08:00-12:00 y 10:00-11:00 (día 0)"


def test_validar_franja_titular_excluye_la_propia_al_editar() -> None:
    existente = _slot(time(8), time(12))
    editada = Slot(
        id=existente.id,
        casilla_id=CASILLA,
        hora_inicio=time(8, 30),
        hora_fin=time(12),
        dia_semana=0,
        sort_order=0,
    )

    validar_franja_titular(editada, [existente])  # no levanta


def test_validar_franja_titular_traduce_a_errores_de_dominio() -> None:
    with pytest.raises(FranjaInvalidaError):
        validar_franja_titular(_slot(time(9), time(8)), [])
    with pytest.raises(FranjasSolapadasError):
        validar_franja_titular(_slot(time(11), time(13)), [_slot(time(8), time(12))])
