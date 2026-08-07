"""Mismo escenario que HelpDeskManager-Web/backend/tests/test_proyeccion.py,
pero de punta a punta contra el módulo nuevo: Excel real -> reader -> dominio
-> writer -> Excel/CSV real. Verifica que el cableado infra+dominio junto da
los mismos números que la app vieja, no solo el dominio aislado."""

import csv
from datetime import date

from openpyxl import Workbook

from src.modules.contadores.application.dtos.run_projection_request import RunProjectionRequest
from src.modules.contadores.application.use_cases.run_counter_projection import (
    RunCounterProjectionUseCase,
)
from src.modules.contadores.infrastructure.excel.openpyxl_counter_workbook_reader import (
    OpenpyxlCounterWorkbookReader,
)
from src.modules.contadores.infrastructure.excel.openpyxl_projection_report_writer import (
    OpenpyxlProjectionReportWriter,
)


def _write_input_workbook(path: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(("Reporte Contadores de Impresoras",))
    ws.append(("Articulo", "Nro Serie", "Sector", "Fecha", "Tipo Contador", "Clase", "Contador"))
    # Serie A: lectura real en la fecha de toma -> REAL
    ws.append(
        ("Kyocera 3560", "SER-A001", "Administracion", "01/03/2026", "Lectura", "Mono", 50000)
    )
    ws.append(
        ("Kyocera 3560", "SER-A001", "Administracion", "15/05/2026", "Lectura", "Mono", 55000)
    )
    # Serie B: sin lectura en la fecha de toma -> PROYECTADO
    ws.append(("HP LaserJet", "SER-B002", "Ventas", "01/02/2026", "Lectura", "Color", 30000))
    ws.append(("HP LaserJet", "SER-B002", "Ventas", "01/04/2026", "Lectura", "Color", 33000))
    wb.save(path)


def test_end_to_end_matches_legacy_projection_numbers(tmp_path) -> None:
    input_path = tmp_path / "contadores.xlsx"
    _write_input_workbook(str(input_path))

    use_case = RunCounterProjectionUseCase(
        OpenpyxlCounterWorkbookReader(), OpenpyxlProjectionReportWriter()
    )
    request = RunProjectionRequest(
        file_path=str(input_path),
        source_filename="contadores.xlsx",
        fecha_toma=date(2026, 5, 15),
        output_dir=str(tmp_path / "out"),
    )

    result = use_case.execute(request)

    assert result.summary.total == 2
    assert result.summary.reales == 1
    assert result.summary.proyectados == 1

    result_b = next(r for r in result.results if r.serie == "SER-B002")
    assert result_b.metodo == "PROYECTADO"
    assert result_b.dias_proyectados == 44
    # 01/02 -> 01/04 son 59 dias, diff=3000 -> 50.8475/dia; 44 dias proyectados
    # desde el 01/04 (contador base 33000) hasta la fecha de toma.
    assert result_b.consumo_diario_promedio == 50.8475
    assert result_b.contador_proyectado == 35237

    with open(result.siges_csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    assert len(rows) == 1
    assert rows[0]["SERIE"] == "SER-B002"
    assert rows[0]["CONTADOR_20"] == str(result_b.contador_proyectado)
