from datetime import date

import pytest

from src.modules.sla.domain.errors import PeriodoInvalidoError
from src.modules.sla.domain.value_objects.periodo import Periodo


def test_expone_anio_y_mes() -> None:
    periodo = Periodo(202608)

    assert periodo.anio == 2026
    assert periodo.mes == 8


@pytest.mark.parametrize("value", [202613, 202600, 2026, 0, -202608])
def test_rechaza_periodos_invalidos(value: int) -> None:
    with pytest.raises(PeriodoInvalidoError):
        Periodo(value)


def test_deriva_primer_y_ultimo_dia_del_mes() -> None:
    periodo = Periodo(202608)

    assert periodo.primer_dia == date(2026, 8, 1)
    assert periodo.ultimo_dia == date(2026, 8, 31)


def test_ultimo_dia_de_febrero_bisiesto() -> None:
    assert Periodo(202402).ultimo_dia == date(2024, 2, 29)
