"""Caracterización: port de `tests/format.test.ts` + las reglas de bitácora de
`incidents.ts` del legacy."""

from datetime import date

from src.modules.reporte_incidentes.domain.entities.incidente import Trabajo
from src.modules.reporte_incidentes.domain.services.bitacora import (
    derivar_solucion,
    descripcion_completa,
    digito_verificador,
    numero_con_digito,
    observacion_de_apertura,
)
from src.modules.reporte_incidentes.domain.value_objects.periodo import (
    Periodo,
    acotar_meses,
    etiqueta_rango,
    meses_entre,
    periodos_recientes,
    rango_periodos,
)


def test_digito_verificador_aplica_ponderacion_ean() -> None:
    assert digito_verificador("2026060001") == "5"


def test_digito_verificador_ignora_lo_que_no_es_digito() -> None:
    assert digito_verificador("INC-2026060001") == "5"


def test_digito_verificador_vacio_sin_digitos() -> None:
    assert digito_verificador("") == digito_verificador("ABC-") == ""


def test_digito_verificador_cierra_el_modulo_a_cero() -> None:
    assert digito_verificador("00") == "0"


def test_numero_con_digito() -> None:
    assert numero_con_digito("2026060001") == "2026060001-5"
    assert numero_con_digito("") == ""


def test_periodos_recientes_hacia_atras_y_cruzando_el_anio() -> None:
    assert [str(p) for p in periodos_recientes(3, date(2026, 6, 15))] == [
        "2026-06", "2026-05", "2026-04",
    ]
    assert [str(p) for p in periodos_recientes(2, date(2026, 1, 10))] == ["2026-01", "2025-12"]


def test_etiqueta_de_periodo_y_de_rango() -> None:
    assert Periodo.parse("2026-06").etiqueta == "Junio 2026"
    assert etiqueta_rango(Periodo.parse("2026-02"), 3) == "Diciembre 2025 – Febrero 2026"


def test_rango_de_periodos_del_mas_viejo_al_mas_nuevo() -> None:
    rango = rango_periodos(Periodo.parse("2026-01"), 3)
    assert [str(p) for p in rango] == ["2025-11", "2025-12", "2026-01"]


def test_meses_entre_es_inclusivo() -> None:
    assert meses_entre(Periodo.parse("2025-11"), Periodo.parse("2026-01")) == 3


def test_acotar_meses_al_rango_1_a_24() -> None:
    assert [acotar_meses(m) for m in (None, 0, 5, 99)] == [1, 1, 5, 24]


def _t(estado: str, descripcion: str = "", observ: str | None = None) -> Trabajo:
    return Trabajo(descripcion=descripcion, observ=observ, estado=estado)


def test_solucion_sale_de_las_instancias_finales() -> None:
    trabajos = [_t("Pendiente", "visita"), _t("Finalizado", "cambio fusor"), _t("Cerrado", "ok")]
    assert derivar_solucion(trabajos) == "cambio fusor · ok"


def test_solucion_sin_finales_usa_todas_las_descripciones() -> None:
    assert derivar_solucion([_t("Pendiente", "a"), _t("En curso", "b")]) == "a · b"
    assert derivar_solucion([_t("Pendiente")]) is None


def test_observacion_sale_de_la_instancia_de_apertura() -> None:
    trabajos = [_t("Derivado", observ="nota interna"), _t("Ingresado", observ="no imprime")]
    assert observacion_de_apertura(trabajos) == "no imprime"
    assert observacion_de_apertura([_t("Derivado", observ="primera")]) == "primera"


def test_descripcion_completa_no_repite_la_observacion() -> None:
    assert descripcion_completa("Atasco", "no imprime") == "Atasco — no imprime"
    assert descripcion_completa("Atasco no imprime", "no imprime") == "Atasco no imprime"
    assert descripcion_completa("", "no imprime") == "no imprime"
