"""Mismos 4 casos verificados en vivo contra /api/contadores/process-db3 el
2026-08-07 (subiendo un DB3 sintético a la app vieja) — ver
CONTADORES_CARACTERIZACION.md."""

from datetime import date

from src.modules.contadores.domain.services.db3_export_builder import build_db3_export_rows
from src.modules.contadores.domain.value_objects.db3_counter_row import Db3CounterRow

_FECHA = date(2026, 8, 5)


def test_normal_classes_10_and_20_merge_into_one_wide_row() -> None:
    rows = [
        Db3CounterRow("SER001", _FECHA, 1000, "ModeloNormal", 10),
        Db3CounterRow("SER001", _FECHA, 200, "ModeloNormal", 20),
    ]

    out = build_db3_export_rows(rows)

    assert len(out) == 1
    row = out[0]
    assert row.tipo == 7
    assert row.clase_10 == "10" and row.contador_10 == 1000
    assert row.clase_20 == "20" and row.contador_20 == 200


def test_total_counter_of_special_model_goes_to_clase_20_only() -> None:
    # Decisión consciente (distinta de la app vieja, ver CONTADORES_CARACTERIZACION.md):
    # la app vieja duplicaba el total en CLASE_10 y CLASE_20, pero eso manda un
    # "mono" mal etiquetado que SiGes rechaza por contador mono faltante/inválido
    # (caso real: equipo 0BLRBJLHC00001B, modelo X4300LX, solo reporta clase 40).
    # Ahora no se carga la columna 10 en absoluto.
    rows = [Db3CounterRow("SER002", _FECHA, 5000, "C4010ND", 40)]

    row = build_db3_export_rows(rows)[0]

    assert row.tipo == 15
    assert row.clase_10 == "20" and row.contador_10 == 5000
    assert row.clase_20 == "" and row.contador_20 == 0


def test_total_counter_of_normal_model_goes_to_clase_10_only() -> None:
    rows = [Db3CounterRow("SER003", _FECHA, 3000, "ModeloNormal", 40)]

    row = build_db3_export_rows(rows)[0]

    assert row.tipo == 15
    assert row.clase_10 == "10" and row.contador_10 == 3000
    assert row.clase_20 == "" and row.contador_20 == 0


def test_irrelevant_counter_class_is_filtered_out() -> None:
    rows = [Db3CounterRow("SER004", _FECHA, 999, "ModeloNormal", 99)]

    assert build_db3_export_rows(rows) == []


def test_color_only_class_20_reading_shifts_left_to_clase_10() -> None:
    # Distinto de "en0": acá SI existe el shift "solo color" (contador_10==0
    # y contador_20>0 -> se mueve a la primera columna).
    rows = [Db3CounterRow("SER005", _FECHA, 700, "ModeloNormal", 20)]

    row = build_db3_export_rows(rows)[0]

    assert row.clase_10 == "20" and row.contador_10 == 700
    assert row.clase_20 == "" and row.contador_20 == 0


def test_dedupes_to_the_most_recent_reading_per_serie_and_clase() -> None:
    rows = [
        Db3CounterRow("SER006", date(2026, 8, 1), 100, "M", 10),
        Db3CounterRow("SER006", date(2026, 8, 10), 500, "M", 10),
    ]

    row = build_db3_export_rows(rows)[0]

    assert row.fecha == date(2026, 8, 10)
    assert row.contador_10 == 500


def test_raw_and_total_readings_of_special_model_dont_collide_in_dedupe() -> None:
    # Regresión: el dedupe deduplicaba por (serie, clase) sin `tipo`, así que
    # una lectura cruda de clase 20 (tipo=7) y el total de un modelo especial
    # (clase 40 -> clase "20", tipo=15) el mismo día competían por la misma
    # clave y una de las dos se perdía en silencio según el orden de llegada.
    rows = [
        Db3CounterRow("SER009", _FECHA, 900, "C4010ND", 10),
        Db3CounterRow("SER009", _FECHA, 300, "C4010ND", 20),
        Db3CounterRow("SER009", _FECHA, 1200, "C4010ND", 40),
    ]

    out = build_db3_export_rows(rows)

    assert len(out) == 2
    raw_row = next(r for r in out if r.tipo == 7)
    total_row = next(r for r in out if r.tipo == 15)
    assert raw_row.clase_10 == "10" and raw_row.contador_10 == 900
    assert raw_row.clase_20 == "20" and raw_row.contador_20 == 300
    assert total_row.clase_10 == "20" and total_row.contador_10 == 1200
    assert total_row.clase_20 == "" and total_row.contador_20 == 0


def test_fecha_maxima_excludes_readings_strictly_after_the_cutoff() -> None:
    rows = [
        Db3CounterRow("SER007", date(2026, 8, 1), 100, "M", 10),
        Db3CounterRow("SER007", date(2026, 8, 10), 500, "M", 10),
    ]

    row = build_db3_export_rows(rows, fecha_maxima=date(2026, 8, 5))[0]

    assert row.contador_10 == 100


def test_fecha_maxima_includes_readings_on_the_cutoff_date() -> None:
    rows = [
        Db3CounterRow("SER008", date(2026, 8, 1), 100, "M", 10),
        Db3CounterRow("SER008", date(2026, 8, 17), 500, "M", 10),
    ]

    row = build_db3_export_rows(rows, fecha_maxima=date(2026, 8, 17))[0]

    assert row.fecha == date(2026, 8, 17)
    assert row.contador_10 == 500
