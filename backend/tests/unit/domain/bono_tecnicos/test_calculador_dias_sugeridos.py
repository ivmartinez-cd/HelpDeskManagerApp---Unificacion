from datetime import date

from src.modules.bono_tecnicos.domain.services.calculador_dias_sugeridos import (
    AusenciaTecnico,
    calcular_dias_sugeridos,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


def _ausencia(desde: date, hasta: date, *, half_day: bool = False) -> AusenciaTecnico:
    return AusenciaTecnico(start_date=desde, end_date=hasta, half_day=half_day)


def test_mayo_2026_sin_ausencias_son_21_dias_habiles() -> None:
    # Mayo 2026: 1 vie, 2 sáb, 3 dom ... 21 días de lunes a viernes en total.
    assert calcular_dias_sugeridos(Periodo(202605), []) == 21


def test_resta_un_dia_completo_de_ausencia() -> None:
    ausencia = _ausencia(date(2026, 5, 4), date(2026, 5, 4))

    assert calcular_dias_sugeridos(Periodo(202605), [ausencia]) == 20


def test_resta_medio_dia_por_half_day() -> None:
    ausencia = _ausencia(date(2026, 5, 4), date(2026, 5, 4), half_day=True)

    assert calcular_dias_sugeridos(Periodo(202605), [ausencia]) == 20  # round(21 - 0.5) = 20


def test_ausencia_fuera_del_periodo_no_descuenta() -> None:
    ausencia = _ausencia(date(2026, 4, 30), date(2026, 4, 30))

    assert calcular_dias_sugeridos(Periodo(202605), [ausencia]) == 21


def test_ausencia_que_cruza_el_borde_del_periodo_solo_cuenta_los_dias_dentro() -> None:
    # Del 29/4 al 4/5: dentro de mayo caen 1(vie) y 4(lun) -> 2 días hábiles.
    ausencia = _ausencia(date(2026, 4, 29), date(2026, 5, 4))

    assert calcular_dias_sugeridos(Periodo(202605), [ausencia]) == 19


def test_ausencia_en_fin_de_semana_no_descuenta_nada_extra() -> None:
    ausencia = _ausencia(date(2026, 5, 2), date(2026, 5, 3))

    assert calcular_dias_sugeridos(Periodo(202605), [ausencia]) == 21


def test_nunca_devuelve_negativo() -> None:
    ausencias = [_ausencia(date(2026, 5, 1), date(2026, 5, 31))]

    assert calcular_dias_sugeridos(Periodo(202605), ausencias) == 0
