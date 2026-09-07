"""ALT011 — Doble Facturación: cobrado = 2 × esperado, en cualquier tipo de
servicio; reemplaza al ALT001 del mismo incidente cuando está activa."""

from src.modules.liquidaciones.domain.services.motor_reglas.motor import ejecutar_motor_reglas
from tests.unit.domain.liquidaciones.factories import (
    make_incidente,
    make_tarifario,
    reglas_activas_default,
)


def _codigos(resultado) -> list[str]:  # noqa: ANN001
    return sorted(a.tipo_alerta for a in resultado.alertas)


class TestAlt011DobleFacturacion:
    def test_dispara_con_el_doble_exacto_y_no_alt001(self) -> None:
        tarifario = make_tarifario(
            costo_servicio=61958.0, tipo_servicio="instalacion_desinstalacion"
        )
        incidente = make_incidente(
            costo_servicio_cobrado=123916.0, tipo="instalacion_desinstalacion"
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert _codigos(resultado) == ["ALT011"]
        alerta = resultado.alertas[0]
        assert alerta.riesgo == 90.0
        assert alerta.datos_contexto == {
            "cobrado": 123916.0,
            "esperado": 61958.0,
            "diferencia": 61958.0,
            "multiplo": 2,
            "tipo_servicio": "instalacion_desinstalacion",
        }
        assert "2 × $61,958.00" in alerta.descripcion

    def test_tambien_en_correctivo(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=3000.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert _codigos(resultado) == ["ALT011"]

    def test_diferencia_que_no_es_el_doble_sigue_siendo_alt001(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=2999.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert _codigos(resultado) == ["ALT001"]

    def test_precio_correcto_no_dispara(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1500.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert resultado.alertas == []

    def test_con_alt011_apagada_el_doble_vuelve_a_ser_alt001(self) -> None:
        reglas = reglas_activas_default()
        del reglas["ALT011"]
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=3000.0)
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [], [tarifario])
        assert _codigos(resultado) == ["ALT001"]

    def test_sin_tarifario_no_dispara(self) -> None:
        incidente = make_incidente(costo_servicio_cobrado=3000.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], []
        )
        assert "ALT011" not in _codigos(resultado)
