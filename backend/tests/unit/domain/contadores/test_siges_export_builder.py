from datetime import date

from src.modules.contadores.domain.services.siges_export_builder import build_siges_rows
from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)


def _result(
    serie: str, clase: str, metodo: str, contador: int | None = 100
) -> CounterProjectionResult:
    return CounterProjectionResult(
        serie=serie,
        clase=clase,
        articulo="X",
        sector="A",
        fecha_lectura=date(2026, 1, 1),
        contador_base=90,
        dias_proyectados=10,
        consumo_diario_promedio=1.0,
        paginas_sumadas=10,
        fecha_toma=date(2026, 1, 11),
        contador_proyectado=contador,
        metodo=metodo,
        observaciones="obs",
    )


def test_series_with_no_projected_class_are_excluded() -> None:
    results = [_result("S1", "Mono", "REAL"), _result("S1", "Color", "REAL")]

    rows = build_siges_rows(results)

    assert rows == []


def test_mono_projected_and_color_real_includes_the_whole_serie() -> None:
    # Regla verificada contra la app vieja: alcanza con que UNA clase sea
    # PROYECTADO para que la serie entera (incluida la clase REAL) entre.
    results = [
        _result("S1", "Mono", "PROYECTADO", contador=150),
        _result("S1", "Color", "REAL", contador=50),
    ]

    rows = build_siges_rows(results)

    assert len(rows) == 1
    row = rows[0]
    assert row.clase_10 == "10" and row.contador_10 == 150
    assert row.clase_20 == "20" and row.contador_20 == 50
    assert row.motivo == "PROYECTADO / REAL"


def test_only_mono_present_leaves_clase_20_empty() -> None:
    results = [_result("S1", "Mono", "PROYECTADO", contador=200)]

    row = build_siges_rows(results)[0]

    assert row.clase_10 == "10" and row.contador_10 == 200
    assert row.clase_20 == "" and row.contador_20 == ""
