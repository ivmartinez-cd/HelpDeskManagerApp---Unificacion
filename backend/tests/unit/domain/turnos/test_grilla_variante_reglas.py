"""Invariantes y advertencias de una grilla variante (ADR-025)."""

import uuid
from datetime import date, time

import pytest

from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante, VarianteSlot
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import (
    InvalidVarianteRangeError,
    VarianteFranjaInvalidaError,
    VarianteFranjasSolapadasError,
    VarianteOperadorSolapadoError,
    VarianteSinFranjasError,
)
from src.modules.turnos.domain.services.grilla_variante_reglas import (
    advertencias_de_cobertura,
    hay_solapamiento_vigencia,
    validar_franjas,
    validar_vigencia,
)
from tests.unit.domain.turnos.caso_majo import CasoMajo

INSUMOS = uuid.uuid4()
ST = uuid.uuid4()


def _franja(
    casilla: uuid.UUID, inicio: time, fin: time, *users: uuid.UUID, dia: int = 0
) -> VarianteSlot:
    return VarianteSlot(
        id=uuid.uuid4(),
        casilla_id=casilla,
        dia_semana=dia,
        hora_inicio=inicio,
        hora_fin=fin,
        sort_order=0,
        user_ids=list(users),
    )


def _variante(desde: date, hasta: date, estado: str = "ACTIVA") -> GrillaVariante:
    return GrillaVariante(
        id=uuid.uuid4(),
        motivo=None,
        origen_texto=None,
        desde=desde,
        hasta=hasta,
        estado=estado,  # type: ignore[arg-type]
        created_by_user_id=uuid.uuid4(),
    )


def test_desde_mayor_que_hasta_es_invalido() -> None:
    with pytest.raises(InvalidVarianteRangeError):
        validar_vigencia(date(2026, 8, 28), date(2026, 8, 24))
    validar_vigencia(date(2026, 8, 24), date(2026, 8, 24))  # un solo día vale


def test_solapamiento_de_vigencia_solo_cuenta_variantes_activas() -> None:
    activa = _variante(date(2026, 8, 24), date(2026, 8, 28))
    cancelada = _variante(date(2026, 8, 24), date(2026, 8, 28), estado="CANCELADA")

    assert hay_solapamiento_vigencia(date(2026, 8, 28), date(2026, 9, 4), [activa]) is True
    assert hay_solapamiento_vigencia(date(2026, 8, 29), date(2026, 9, 4), [activa]) is False
    assert hay_solapamiento_vigencia(date(2026, 8, 24), date(2026, 8, 28), [cancelada]) is False


def test_variante_sin_franjas_es_invalida() -> None:
    with pytest.raises(VarianteSinFranjasError):
        validar_franjas([])


def test_franja_con_inicio_mayor_o_igual_que_fin_es_invalida() -> None:
    with pytest.raises(VarianteFranjaInvalidaError):
        validar_franjas([_franja(INSUMOS, time(11), time(8))])
    with pytest.raises(VarianteFranjaInvalidaError):
        validar_franjas([_franja(INSUMOS, time(8), time(8))])


def test_franjas_de_la_misma_casilla_y_dia_no_se_superponen() -> None:
    with pytest.raises(VarianteFranjasSolapadasError):
        validar_franjas(
            [_franja(INSUMOS, time(8), time(11)), _franja(INSUMOS, time(10), time(13))]
        )
    # Contiguas (fin == inicio) y en distinto día sí valen
    validar_franjas(
        [
            _franja(INSUMOS, time(8), time(11)),
            _franja(INSUMOS, time(11), time(13)),
            _franja(INSUMOS, time(8), time(13), dia=1),
        ]
    )


def test_mismo_operador_en_franjas_solapadas_de_distinta_casilla_es_error() -> None:
    luna = uuid.uuid4()
    with pytest.raises(VarianteOperadorSolapadoError):
        validar_franjas(
            [_franja(INSUMOS, time(11), time(13), luna), _franja(ST, time(12), time(14), luna)]
        )
    # El mismo operador en franjas contiguas o de distinto día no es problema
    validar_franjas(
        [
            _franja(INSUMOS, time(11), time(13), luna),
            _franja(ST, time(13), time(14), luna),
            _franja(ST, time(12), time(14), luna, dia=2),
        ]
    )


def test_los_huecos_respecto_de_la_titular_son_advertencia_no_error() -> None:
    caso = CasoMajo()
    variante = caso.variante_esperada()
    validar_franjas(variante.slots)  # no lanza

    advertencias = advertencias_de_cobertura(variante.slots, caso.slots)

    huecos = [(a.dia_semana, a.hora_inicio, a.hora_fin) for a in advertencias if a.tipo == "HUECO"]
    # INSUMOS abre 8:30 en la variante: 8:00-8:30 sin cobertura, los 5 días L-V
    assert huecos == [(dia, time(8), time(8, 30)) for dia in range(5)]
    assert all(a.casilla_id == caso.insumos.id for a in advertencias if a.tipo == "HUECO")
    # ST 8-9 es cobertura nueva (no existía en la titular): no es hueco


def test_franja_sin_operador_es_advertencia() -> None:
    titular = [
        Slot(
            id=uuid.uuid4(),
            casilla_id=INSUMOS,
            hora_inicio=time(8),
            hora_fin=time(11),
            dia_semana=0,
            sort_order=0,
        )
    ]
    advertencias = advertencias_de_cobertura([_franja(INSUMOS, time(8), time(11))], titular)

    assert [a.tipo for a in advertencias] == ["SIN_OPERADOR"]


def test_hueco_en_el_medio_y_dia_sin_franjas() -> None:
    titular = [
        Slot(
            id=uuid.uuid4(),
            casilla_id=INSUMOS,
            hora_inicio=time(8),
            hora_fin=time(18),
            dia_semana=dia,
            sort_order=0,
        )
        for dia in (0, 1)
    ]
    variante = [
        _franja(INSUMOS, time(8), time(12), uuid.uuid4()),
        _franja(INSUMOS, time(13), time(18), uuid.uuid4()),
    ]
    huecos = [
        (a.dia_semana, a.hora_inicio, a.hora_fin)
        for a in advertencias_de_cobertura(variante, titular)
        if a.tipo == "HUECO"
    ]
    assert huecos == [(0, time(12), time(13)), (1, time(8), time(18))]
