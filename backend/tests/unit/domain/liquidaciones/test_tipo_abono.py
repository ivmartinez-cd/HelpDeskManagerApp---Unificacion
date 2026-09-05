"""Detección de liquidaciones de abono y reglas que aplican a cada tipo."""

from src.modules.liquidaciones.domain.entities.liquidacion import TIPO_ABONO, TIPO_REGULAR
from src.modules.liquidaciones.domain.services.tipo_abono import (
    es_abono,
    reglas_aplicables,
    tipo_segun_incidentes,
)
from tests.unit.domain.liquidaciones.factories import make_incidente, reglas_activas_default


class TestEsAbono:
    def test_todos_a_un_peso_es_abono(self) -> None:
        incidentes = [make_incidente(costo_servicio_cobrado=1.0) for _ in range(3)]
        assert es_abono(incidentes)
        assert tipo_segun_incidentes(incidentes) == TIPO_ABONO

    def test_uno_con_precio_real_no_es_abono(self) -> None:
        incidentes = [
            make_incidente(costo_servicio_cobrado=1.0),
            make_incidente(costo_servicio_cobrado=54400.0),
        ]
        assert not es_abono(incidentes)
        assert tipo_segun_incidentes(incidentes) == TIPO_REGULAR

    def test_sin_incidentes_no_es_abono(self) -> None:
        assert not es_abono([])
        assert tipo_segun_incidentes([]) == TIPO_REGULAR


class TestReglasAplicables:
    def test_regular_corre_todas_las_activas(self) -> None:
        activas = reglas_activas_default()
        assert reglas_aplicables(TIPO_REGULAR, activas) == dict(activas)

    def test_abono_apaga_precio_y_km_pero_deja_duplicados(self) -> None:
        activas = reglas_activas_default()
        aplicables = reglas_aplicables(TIPO_ABONO, activas)
        assert "ALT001" not in aplicables
        assert "ALT002" not in aplicables
        assert "ALT008" not in aplicables
        assert set(aplicables) == {c for c in activas if c in {"ALT004", "ALT010"}}
