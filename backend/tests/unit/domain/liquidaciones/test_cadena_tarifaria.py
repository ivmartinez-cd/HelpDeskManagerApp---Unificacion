"""Tests de recalcular_cadena — cadena temporal de vigencias de tarifarios."""

import uuid
from datetime import date

from src.modules.liquidaciones.domain.services.cadena_tarifaria import recalcular_cadena
from tests.unit.domain.liquidaciones.factories import make_tarifario

PRESTADOR_ID = uuid.uuid4()


def _tarifa(desde: date, hasta: date | None = None, **overrides):
    return make_tarifario(
        prestador_id=PRESTADOR_ID, vigencia_desde=desde, vigencia_hasta=hasta, **overrides
    )


class TestRecalcularCadena:
    def test_cadena_vacia_o_unitaria_no_genera_ajustes(self) -> None:
        assert recalcular_cadena([]) == []
        assert recalcular_cadena([_tarifa(date(2026, 1, 1))]) == []

    def test_cierra_cada_tarifa_el_dia_anterior_a_la_siguiente(self) -> None:
        vieja = _tarifa(date(2026, 1, 1))
        nueva = _tarifa(date(2026, 4, 1))

        ajustes = recalcular_cadena([nueva, vieja])

        assert len(ajustes) == 1
        assert ajustes[0].tarifario_id == vieja.id
        assert ajustes[0].vigencia_hasta == date(2026, 3, 31)

    def test_la_ultima_tarifa_conserva_su_vigencia_hasta(self) -> None:
        vieja = _tarifa(date(2026, 1, 1))
        nueva = _tarifa(date(2026, 4, 1), hasta=date(2026, 12, 31))

        ajustes = recalcular_cadena([vieja, nueva])

        assert [a.tarifario_id for a in ajustes] == [vieja.id]

    def test_no_ajusta_filas_ya_encadenadas(self) -> None:
        vieja = _tarifa(date(2026, 1, 1), hasta=date(2026, 3, 31))
        nueva = _tarifa(date(2026, 4, 1))

        assert recalcular_cadena([vieja, nueva]) == []

    def test_insertar_en_el_medio_reencadena_ambos_lados(self) -> None:
        primera = _tarifa(date(2026, 1, 1), hasta=date(2026, 5, 31))
        ultima = _tarifa(date(2026, 6, 1))
        intermedia = _tarifa(date(2026, 3, 1))

        ajustes = {a.tarifario_id: a.vigencia_hasta for a in
                   recalcular_cadena([primera, ultima, intermedia])}

        assert ajustes == {
            primera.id: date(2026, 2, 28),
            intermedia.id: date(2026, 5, 31),
        }
