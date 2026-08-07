"""Mismos 3 casos verificados en vivo contra /api/tools/en0 el 2026-08-07
(la implementación real en counters_tools.py, no csv_en0.py que es código
muerto) — ver CONTADORES_CARACTERIZACION.md."""

import pytest

from src.modules.contadores.domain.errors import NoFaltaContadorRowsError
from src.modules.contadores.domain.services.estimation_zero_builder import (
    build_estimation_zero_rows,
)
from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)


def test_mono_and_color_rows_go_to_different_wide_columns() -> None:
    source = [
        FaltaContadorSourceRow("FALTA CONTADOR Mono", "SER100", 1500, "Mono"),
        FaltaContadorSourceRow("FALTA CONTADOR Color", "SER101", 300, "Color"),
        FaltaContadorSourceRow("OK", "SER102", 999, "Mono"),
    ]

    rows = build_estimation_zero_rows(source, "07/08/2026")

    by_serie = {r.serie: r for r in rows}
    assert set(by_serie) == {"SER100", "SER101"}  # SER102 filtrada (Tipo "OK")
    assert by_serie["SER100"].clase_10 == "10" and by_serie["SER100"].contador_10 == 1500
    # Sin "shift": Color queda en CLASE_20, no se mueve a CLASE_10.
    assert by_serie["SER101"].clase_20 == "20" and by_serie["SER101"].contador_20 == 300
    assert by_serie["SER101"].clase_10 == "" and by_serie["SER101"].contador_10 == 0


def test_tipo_match_is_case_insensitive_substring() -> None:
    source = [FaltaContadorSourceRow("falta contador mono", "SER1", 100, "Mono")]

    rows = build_estimation_zero_rows(source, "07/08/2026")

    assert len(rows) == 1


def test_missing_nombre_clase_leaves_both_columns_empty() -> None:
    source = [FaltaContadorSourceRow("FALTA CONTADOR", "SER1", 100, None)]

    row = build_estimation_zero_rows(source, "07/08/2026")[0]

    assert row.clase_10 == "" and row.clase_20 == ""


def test_no_matching_rows_raises() -> None:
    source = [FaltaContadorSourceRow("OK", "SER1", 100, "Mono")]

    with pytest.raises(NoFaltaContadorRowsError):
        build_estimation_zero_rows(source, "07/08/2026")
