"""Apertura lazy de ciclos (D7): año actual siempre abierto; año+1 desde la
fecha configurada inclusive; flag almacenado prevalece."""

from datetime import date

from src.modules.vacaciones.domain.services.ciclo_policy import (
    apertura_efectiva,
    fecha_apertura_proximo_ciclo,
    is_open_por_politica,
)
from tests.unit.domain.vacaciones.factories import make_config

CONFIG = make_config()  # apertura 1/10


class TestIsOpenPorPolitica:
    def test_anio_actual_siempre_abierto(self) -> None:
        assert is_open_por_politica(2026, date(2026, 1, 1), CONFIG) is True

    def test_anio_siguiente_cerrado_antes_de_la_apertura(self) -> None:
        assert is_open_por_politica(2027, date(2026, 9, 30), CONFIG) is False

    def test_anio_siguiente_abre_el_dia_exacto_inclusive(self) -> None:
        assert is_open_por_politica(2027, date(2026, 10, 1), CONFIG) is True

    def test_anio_pasado_cerrado(self) -> None:
        assert is_open_por_politica(2025, date(2026, 8, 13), CONFIG) is False

    def test_mas_de_un_anio_adelante_cerrado(self) -> None:
        assert is_open_por_politica(2028, date(2026, 12, 31), CONFIG) is False


class TestAperturaEfectiva:
    def test_flag_almacenado_true_prevalece(self) -> None:
        assert apertura_efectiva(True, 2025, date(2026, 8, 13), CONFIG) is True

    def test_flag_false_cae_en_la_politica(self) -> None:
        assert apertura_efectiva(False, 2026, date(2026, 8, 13), CONFIG) is True


class TestFechaApertura:
    def test_usa_dia_y_mes_de_la_config_en_el_anio_actual(self) -> None:
        assert fecha_apertura_proximo_ciclo(date(2026, 8, 13), CONFIG) == date(2026, 10, 1)
