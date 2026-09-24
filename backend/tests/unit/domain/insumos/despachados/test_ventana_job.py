"""Tests de la ventana horaria del job programado de Despachados.

La semana de referencia arranca el lunes 21/09/2026; los momentos ya están en hora
Argentina (la conversión es de quien llama).
"""

from datetime import datetime

import pytest

from src.modules.insumos.domain.services.despachados.ventana_job import (
    VentanaJob,
    dentro_de_ventana,
)

LUNES_A_SABADO_8_A_20 = VentanaJob(dias_semana=frozenset(range(6)), hora_inicio=8, hora_fin=20)


def _el(dia: int, hora: int, minuto: int = 0) -> datetime:
    """`dia` de septiembre de 2026 (21 = lunes, 26 = sábado, 27 = domingo)."""
    return datetime(2026, 9, dia, hora, minuto)


@pytest.mark.parametrize(
    ("momento", "esperado"),
    [
        pytest.param(_el(21, 8), True, id="lunes-8-en-punto"),
        pytest.param(_el(23, 13, 30), True, id="miercoles-al-mediodia"),
        pytest.param(_el(26, 19, 59), True, id="sabado-19-59"),
        pytest.param(_el(21, 7, 59), False, id="lunes-antes-de-las-8"),
        pytest.param(_el(25, 20), False, id="viernes-20-en-punto"),
        pytest.param(_el(27, 12), False, id="domingo"),
    ],
)
def test_dentro_de_ventana(momento: datetime, esperado: bool) -> None:
    assert dentro_de_ventana(momento, LUNES_A_SABADO_8_A_20) is esperado


def test_una_ventana_de_todo_el_dia() -> None:
    siempre = VentanaJob(dias_semana=frozenset(range(7)), hora_inicio=0, hora_fin=24)

    assert dentro_de_ventana(_el(27, 0), siempre) is True
    assert dentro_de_ventana(_el(27, 23, 59), siempre) is True


@pytest.mark.parametrize(
    ("inicio", "fin"),
    [
        pytest.param(20, 8, id="invertida"),
        pytest.param(8, 8, id="vacia"),
        pytest.param(-1, 20, id="inicio-negativo"),
        pytest.param(8, 25, id="fin-despues-de-medianoche"),
    ],
)
def test_rechaza_horarios_invalidos(inicio: int, fin: int) -> None:
    with pytest.raises(ValueError, match="0 <= inicio < fin <= 24"):
        VentanaJob(dias_semana=frozenset({0}), hora_inicio=inicio, hora_fin=fin)


def test_rechaza_dias_fuera_de_la_semana() -> None:
    with pytest.raises(ValueError, match=r"\[7\]"):
        VentanaJob(dias_semana=frozenset({0, 7}), hora_inicio=8, hora_fin=20)


def test_rechaza_una_ventana_sin_dias() -> None:
    with pytest.raises(ValueError, match="al menos un día"):
        VentanaJob(dias_semana=frozenset(), hora_inicio=8, hora_fin=20)
