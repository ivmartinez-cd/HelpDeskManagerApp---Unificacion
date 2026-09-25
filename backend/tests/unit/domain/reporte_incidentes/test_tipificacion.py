from src.modules.reporte_incidentes.domain.entities.categoria import TipificacionGuardada
from src.modules.reporte_incidentes.domain.services.tipificacion import (
    PENDIENTE,
    aplicar_umbral,
    clave_caso,
    tipificar_desde_cache,
)
from src.modules.reporte_incidentes.domain.services.ventana import top_para
from src.modules.reporte_incidentes.domain.value_objects.periodo import Periodo
from tests.unit.domain.reporte_incidentes.fakes import incidente

_ALTA = TipificacionGuardada("Hardware y Desgaste", "Escaner / ADF", "alta")


def test_clave_de_caso_como_el_legacy() -> None:
    inc = incidente(descripcion="Atasco", causa=None, solucion="cambio rodillo")
    assert clave_caso(inc) == "Atasco||cambio rodillo"


def test_solo_la_confianza_alta_se_muestra() -> None:
    assert aplicar_umbral(_ALTA) == ("Hardware y Desgaste", "Escaner / ADF")
    assert aplicar_umbral(TipificacionGuardada("X", "Y", "media")) == (PENDIENTE, "")
    assert aplicar_umbral(TipificacionGuardada("X", "Y", "ALTA")) == ("X", "Y")


def test_tipificar_desde_cache_cuenta_casos_distintos_sin_tipificar() -> None:
    tipificado = incidente(descripcion="a")
    sin_cache = [incidente(descripcion="b"), incidente(descripcion="b"), incidente(descripcion="c")]
    r = tipificar_desde_cache([tipificado, *sin_cache], {clave_caso(tipificado): _ALTA})
    assert r.pendientes == 2
    assert r.incidentes[0].categoria == "Hardware y Desgaste"
    assert {i.categoria for i in r.incidentes[1:]} == {PENDIENTE}


def test_sin_descripcion_no_se_tipifica_ni_cuenta_como_pendiente() -> None:
    inc = incidente(descripcion="")
    r = tipificar_desde_cache([inc], {clave_caso(inc): _ALTA})
    assert (r.pendientes, r.incidentes[0].categoria) == (0, PENDIENTE)


def test_top_depende_de_que_tan_atras_esta_el_mes_mas_viejo() -> None:
    actual = Periodo.parse("2026-09")
    assert top_para(Periodo.parse("2026-09"), actual, 500) == 500
    assert top_para(Periodo.parse("2025-07"), actual, 500) == 15 * 500
