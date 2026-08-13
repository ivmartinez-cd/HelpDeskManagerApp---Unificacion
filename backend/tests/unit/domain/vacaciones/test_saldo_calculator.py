"""Cadena de saldos con carry-over iterativo (equivalencia con la recursión
del legacy, caso base 2026)."""

from src.modules.vacaciones.domain.services.saldo_calculator import (
    ANIO_BASE_CARRY_OVER,
    ConsumoAnual,
    ReglasCarryOver,
    calcular_cadena_saldos,
)

REGLAS_DEFAULT = ReglasCarryOver(allow_carry_over=True, max_carry_over_days=0)


class TestCalcularCadenaSaldos:
    def test_anio_base_no_recibe_carry(self) -> None:
        saldos = calcular_cadena_saldos(
            2026, {2026: 14}, {2026: ConsumoAnual(used=5, pending=2)}, REGLAS_DEFAULT
        )
        assert saldos[2026].carry_over == 0
        assert saldos[2026].available == 7

    def test_cadena_de_tres_anios_arrastra_disponibles(self) -> None:
        saldos = calcular_cadena_saldos(
            2028,
            {2026: 14, 2027: 14, 2028: 21},
            {2026: ConsumoAnual(used=4, pending=0)},
            REGLAS_DEFAULT,
        )
        assert saldos[2026].available == 10
        assert saldos[2027].carry_over == 10
        assert saldos[2027].available == 24
        assert saldos[2028].carry_over == 24
        assert saldos[2028].available == 45

    def test_max_carry_over_days_topa_el_arrastre(self) -> None:
        reglas = ReglasCarryOver(allow_carry_over=True, max_carry_over_days=5)
        saldos = calcular_cadena_saldos(
            2028, {2026: 14, 2027: 14, 2028: 21}, {}, reglas
        )
        assert saldos[2027].carry_over == 5
        assert saldos[2028].carry_over == 5

    def test_allow_carry_over_false_anula_el_arrastre(self) -> None:
        reglas = ReglasCarryOver(allow_carry_over=False, max_carry_over_days=0)
        saldos = calcular_cadena_saldos(2027, {2026: 14, 2027: 14}, {}, reglas)
        assert saldos[2027].carry_over == 0
        assert saldos[2027].available == 14

    def test_disponible_negativo_no_arrastra(self) -> None:
        saldos = calcular_cadena_saldos(
            2027,
            {2026: 14, 2027: 14},
            {2026: ConsumoAnual(used=20, pending=0)},
            REGLAS_DEFAULT,
        )
        assert saldos[2026].available == -6
        assert saldos[2027].carry_over == 0

    def test_pending_resta_igual_que_approved(self) -> None:
        saldos = calcular_cadena_saldos(
            2026, {2026: 14}, {2026: ConsumoAnual(used=0, pending=14)}, REGLAS_DEFAULT
        )
        assert saldos[2026].available == 0

    def test_anio_anterior_a_la_base_es_un_solo_anio_sin_carry(self) -> None:
        saldos = calcular_cadena_saldos(2025, {2025: 14}, {}, REGLAS_DEFAULT)
        assert list(saldos) == [2025]
        assert saldos[2025].carry_over == 0

    def test_la_base_es_2026(self) -> None:
        assert ANIO_BASE_CARRY_OVER == 2026
