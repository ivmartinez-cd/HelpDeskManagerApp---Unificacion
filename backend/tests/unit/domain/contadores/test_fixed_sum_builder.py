"""Mismos 5 casos verificados en vivo contra /api/tools/suma-fija el
2026-08-07 — ver CONTADORES_CARACTERIZACION.md."""

from src.modules.contadores.domain.services.fixed_sum_builder import build_fixed_sum_rows
from src.modules.contadores.domain.value_objects.fixed_sum_source_row import FixedSumSourceRow


def test_activa_en_cliente_sums_hojas() -> None:
    source = [FixedSumSourceRow("SERA", "Activa en Cliente", 500)]

    row = build_fixed_sum_rows(source, "07/08/2026", 1000)[0]

    assert row.contador == 1500


def test_desaparecida_is_left_unchanged() -> None:
    source = [FixedSumSourceRow("SERB", "Desaparecida", 800)]

    row = build_fixed_sum_rows(source, "07/08/2026", 1000)[0]

    assert row.contador == 800


def test_backup_fijo_is_left_unchanged() -> None:
    source = [FixedSumSourceRow("SERC", "Backup Fijo", 300)]

    row = build_fixed_sum_rows(source, "07/08/2026", 1000)[0]

    assert row.contador == 300


def test_contador_igual_a_uno_gana_sobre_activa_en_cliente() -> None:
    # El chequeo de Cdor Actual==1 tiene prioridad sobre el de Estado, aunque
    # el Estado sea "Activa en Cliente" (verificado en vivo).
    source = [FixedSumSourceRow("SERD", "Activa en Cliente", 1)]

    row = build_fixed_sum_rows(source, "07/08/2026", 1000)[0]

    assert row.contador == 1


def test_unknown_estado_leaves_contador_empty() -> None:
    source = [FixedSumSourceRow("SERE", "Otro Estado", 700)]

    row = build_fixed_sum_rows(source, "07/08/2026", 1000)[0]

    assert row.contador == ""


def test_output_uses_narrow_format_with_fixed_tipo_and_clase() -> None:
    source = [FixedSumSourceRow("SERA", "Activa en Cliente", 500)]

    row = build_fixed_sum_rows(source, "07/08/2026", 1000)[0]

    assert row.fecha == "07/08/2026"
    assert row.tipo == "14"
    assert row.clase == "10"
