"""Acuerdos de precio por cliente: resolución y efecto sobre ALT001."""

from datetime import date

from src.modules.liquidaciones.domain.services.acuerdos_precio import resolver_acuerdo
from src.modules.liquidaciones.domain.services.motor_reglas.alt001_precio import evaluar_alt001
from tests.unit.domain.liquidaciones.factories import (
    make_acuerdo,
    make_incidente,
    make_tarifario,
)

_FECHA = date(2026, 6, 15)


class TestResolverAcuerdo:
    def test_matchea_por_cliente_normalizado(self) -> None:
        acuerdo = make_acuerdo(empresa_nombre="Minera del Altiplano")
        inc = make_incidente(empresa_nombre="MINERA DEL ALTIPLANO ", fecha_cierre=_FECHA)
        assert resolver_acuerdo(inc, [acuerdo]) is acuerdo

    def test_otro_cliente_no_matchea(self) -> None:
        acuerdo = make_acuerdo(empresa_nombre="Refinor")
        inc = make_incidente(empresa_nombre="YAGUAR", fecha_cierre=_FECHA)
        assert resolver_acuerdo(inc, [acuerdo]) is None

    def test_fuera_de_vigencia_no_aplica(self) -> None:
        acuerdo = make_acuerdo(vigencia_desde=date(2026, 7, 1))
        inc = make_incidente(empresa_nombre="Minera del Altiplano", fecha_cierre=_FECHA)
        assert resolver_acuerdo(inc, [acuerdo]) is None

    def test_tipo_especifico_gana_sobre_general(self) -> None:
        general = make_acuerdo(tipo_servicio=None, factor=2.0)
        especifico = make_acuerdo(tipo_servicio="preventivo", factor=1.5)
        inc = make_incidente(
            empresa_nombre="Minera del Altiplano", tipo="preventivo", fecha_cierre=_FECHA
        )
        assert resolver_acuerdo(inc, [general, especifico]) is especifico

    def test_tipo_distinto_no_aplica(self) -> None:
        acuerdo = make_acuerdo(tipo_servicio="preventivo")
        inc = make_incidente(
            empresa_nombre="Minera del Altiplano", tipo="correctivo", fecha_cierre=_FECHA
        )
        assert resolver_acuerdo(inc, [acuerdo]) is None


class TestAlt001ConAcuerdo:
    def test_precio_doble_acordado_no_alerta(self) -> None:
        tarifario = make_tarifario(costo_servicio=46073.0)
        inc = make_incidente(costo_servicio_cobrado=92146.0, fecha_cierre=_FECHA)
        assert evaluar_alt001(inc, tarifario, make_acuerdo(factor=2.0)) == []

    def test_cobra_distinto_al_acuerdo_alerta_contra_el_acuerdo(self) -> None:
        tarifario = make_tarifario(costo_servicio=46073.0)
        inc = make_incidente(costo_servicio_cobrado=46073.0, fecha_cierre=_FECHA)
        acuerdo = make_acuerdo(factor=2.0, motivo="Costo doble aprobado por AO")

        hallazgos = evaluar_alt001(inc, tarifario, acuerdo)

        assert len(hallazgos) == 1
        assert "acuerdo con Minera del Altiplano" in hallazgos[0].descripcion
        assert "Costo doble aprobado por AO" in hallazgos[0].descripcion
        assert hallazgos[0].contexto["esperado"] == 92146.0
        assert hallazgos[0].contexto["acuerdo_id"] == str(acuerdo.id)

    def test_precio_fijo_no_necesita_tarifario(self) -> None:
        inc = make_incidente(costo_servicio_cobrado=78119.0, fecha_cierre=_FECHA)
        acuerdo = make_acuerdo(factor=None, precio_fijo=78119.0, empresa_nombre="Refinor")
        assert evaluar_alt001(inc, None, acuerdo) == []

    def test_sin_acuerdo_compara_contra_el_tarifario(self) -> None:
        tarifario = make_tarifario(costo_servicio=46073.0)
        inc = make_incidente(costo_servicio_cobrado=92146.0, fecha_cierre=_FECHA)
        hallazgos = evaluar_alt001(inc, tarifario)
        assert len(hallazgos) == 1
        assert "del tarifario" in hallazgos[0].descripcion
        assert "acuerdo_id" not in hallazgos[0].contexto
