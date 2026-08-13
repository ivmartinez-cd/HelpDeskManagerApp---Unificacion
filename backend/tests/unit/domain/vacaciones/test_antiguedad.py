"""Días anuales por antigüedad (divisor 365.25 del legacy, ref = 1/1 del año,
tiers min inclusive / max exclusivo)."""

from datetime import date

from src.modules.vacaciones.domain.services.antiguedad import (
    dias_por_antiguedad,
    referencia_para_anio,
)
from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier
from tests.unit.domain.vacaciones.factories import TIERS_LEGACY

REF_2026 = date(2026, 1, 1)


class TestDiasPorAntiguedad:
    def test_menos_de_medio_anio_da_el_primer_tier(self) -> None:
        # 182 días / 365.25 = 0.498 < 0.5
        assert dias_por_antiguedad(date(2025, 7, 3), REF_2026, TIERS_LEGACY) == 7

    def test_borde_medio_anio_pasa_al_segundo_tier(self) -> None:
        # 183 días / 365.25 = 0.501 >= 0.5
        assert dias_por_antiguedad(date(2025, 7, 2), REF_2026, TIERS_LEGACY) == 14

    def test_borde_cinco_anios_exclusivo(self) -> None:
        # 2021-01-01 → 1826 días = 4.999 años (sigue en 14)
        assert dias_por_antiguedad(date(2021, 1, 1), REF_2026, TIERS_LEGACY) == 14
        # 2020-12-31 → 1827 días = 5.001 años (pasa a 21)
        assert dias_por_antiguedad(date(2020, 12, 31), REF_2026, TIERS_LEGACY) == 21

    def test_supera_el_ultimo_tier_devuelve_el_ultimo(self) -> None:
        assert dias_por_antiguedad(date(1920, 1, 1), REF_2026, TIERS_LEGACY) == 35

    def test_tiers_desordenados_se_ordenan_por_min_years(self) -> None:
        desordenados = (
            SeniorityTier(min_years=5, max_years=10, days=21),
            SeniorityTier(min_years=0, max_years=5, days=10),
        )
        assert dias_por_antiguedad(date(2024, 1, 1), REF_2026, desordenados) == 10

    def test_sin_tiers_usa_los_defaults_del_legacy(self) -> None:
        # 2 años de antigüedad → default 0.5-5 → 14
        assert dias_por_antiguedad(date(2024, 1, 1), REF_2026, ()) == 14


class TestReferenciaParaAnio:
    def test_es_el_primero_de_enero(self) -> None:
        assert referencia_para_anio(2027) == date(2027, 1, 1)
