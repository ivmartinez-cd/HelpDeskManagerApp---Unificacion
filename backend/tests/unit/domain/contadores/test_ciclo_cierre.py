from datetime import date

from src.modules.contadores.domain.services.ciclo_cierre import ventana_periodo_actual


def test_antes_del_cierre_ventana_es_el_periodo_202607() -> None:
    """14/08/2026 todavía factura el período 202607 (20/7 al 20/8)."""
    inicio, fin = ventana_periodo_actual(date(2026, 8, 14))
    assert (inicio, fin) == (date(2026, 7, 20), date(2026, 8, 20))


def test_el_dia_del_cierre_todavia_cuenta_como_antes() -> None:
    inicio, fin = ventana_periodo_actual(date(2026, 8, 20))
    assert (inicio, fin) == (date(2026, 7, 20), date(2026, 8, 20))


def test_despues_del_cierre_ventana_es_el_periodo_202608() -> None:
    """27/08/2026 (día siguiente al cierre) ya está en el período 202608
    (20/8 al 20/9)."""
    inicio, fin = ventana_periodo_actual(date(2026, 8, 27))
    assert (inicio, fin) == (date(2026, 8, 20), date(2026, 9, 20))


def test_arrastre_en_diciembre_cruza_de_anio() -> None:
    inicio, fin = ventana_periodo_actual(date(2026, 12, 25))
    assert (inicio, fin) == (date(2026, 12, 20), date(2027, 1, 20))


def test_antes_del_cierre_en_enero_ventana_viene_de_diciembre() -> None:
    inicio, fin = ventana_periodo_actual(date(2027, 1, 5))
    assert (inicio, fin) == (date(2026, 12, 20), date(2027, 1, 20))
