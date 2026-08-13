"""Conteo de días corridos con extensión LCT (calendarDaysBetween legacy).

Semana de referencia: lunes 2026-08-10 … domingo 2026-08-16.
"""

from datetime import date

from src.modules.vacaciones.domain.services.dias_solicitados import (
    dias_corridos,
    dias_solicitados,
)

LUNES = date(2026, 8, 10)
JUEVES = date(2026, 8, 13)
VIERNES = date(2026, 8, 14)
SABADO = date(2026, 8, 15)
DOMINGO = date(2026, 8, 16)


class TestDiasCorridos:
    def test_fin_viernes_extiende_hasta_el_domingo(self) -> None:
        assert dias_corridos(LUNES, VIERNES) == 7

    def test_fin_sabado_extiende_hasta_el_domingo(self) -> None:
        assert dias_corridos(LUNES, SABADO) == 7

    def test_fin_domingo_no_extiende(self) -> None:
        assert dias_corridos(LUNES, DOMINGO) == 7

    def test_fin_jueves_no_extiende(self) -> None:
        assert dias_corridos(LUNES, JUEVES) == 4

    def test_rango_de_un_dia_habil(self) -> None:
        assert dias_corridos(JUEVES, JUEVES) == 1

    def test_rango_de_un_dia_viernes_extiende_a_tres(self) -> None:
        assert dias_corridos(VIERNES, VIERNES) == 3

    def test_fin_anterior_al_inicio_da_cero(self) -> None:
        assert dias_corridos(VIERNES, LUNES) == 0


class TestDiasSolicitados:
    def test_feriado_no_deduce_en_inicio_resta_un_dia(self) -> None:
        assert dias_solicitados(LUNES, JUEVES, feriado_no_deduce_en_inicio=True) == 3

    def test_sin_feriado_en_inicio_no_resta(self) -> None:
        assert dias_solicitados(LUNES, JUEVES, feriado_no_deduce_en_inicio=False) == 4

    def test_nunca_devuelve_negativo(self) -> None:
        assert dias_solicitados(VIERNES, LUNES, feriado_no_deduce_en_inicio=True) == 0
