from openpyxl import Workbook

from src.modules.contadores.application.dtos.run_estimation_zero_request import (
    RunEstimationZeroRequest,
)
from src.modules.contadores.application.dtos.run_fixed_sum_request import RunFixedSumRequest
from src.modules.contadores.application.use_cases.run_estimation_zero import (
    RunEstimationZeroUseCase,
)
from src.modules.contadores.application.use_cases.run_fixed_sum import RunFixedSumUseCase
from src.modules.contadores.infrastructure.csv.csv_estimation_zero_writer import (
    CsvEstimationZeroWriter,
)
from src.modules.contadores.infrastructure.csv.csv_falta_contador_reader import (
    CsvFaltaContadorReader,
)
from src.modules.contadores.infrastructure.csv.csv_fixed_sum_writer import CsvFixedSumWriter
from src.modules.contadores.infrastructure.excel.openpyxl_fixed_sum_reader import (
    OpenpyxlFixedSumReader,
)


def test_estimation_zero_end_to_end_with_real_csv(tmp_path) -> None:
    input_path = tmp_path / "en0_muestra.csv"
    input_path.write_text(
        "Nro_serie,Tipo,NombreClase,ImpreContadorAnterior\n"
        "SER100,FALTA CONTADOR Mono,Mono,1500\n"
        "SER101,FALTA CONTADOR Color,Color,300\n"
        "SER102,OK,Mono,999\n",
        encoding="utf-8",
    )

    use_case = RunEstimationZeroUseCase(CsvFaltaContadorReader(), CsvEstimationZeroWriter())
    request = RunEstimationZeroRequest(
        file_path=str(input_path),
        cliente="ClienteTest",
        fecha_nueva="07/08/2026",
        output_dir=str(tmp_path / "out"),
    )

    csv_path = use_case.execute(request)

    with open(csv_path, encoding="utf-8") as f:
        content = f.read()
    assert "SER100;07/08/2026;14;10;1500;;0;;" in content
    assert "SER101;07/08/2026;14;;0;20;300;;" in content
    assert "SER102" not in content


def test_fixed_sum_end_to_end_with_real_xlsx(tmp_path) -> None:
    input_path = tmp_path / "suma_muestra.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(("Nro Serie", "Estado", "Cdor Actual"))
    ws.append(("SERA", "Activa en Cliente", 500))
    ws.append(("SERD", "Activa en Cliente", 1))
    wb.save(input_path)

    use_case = RunFixedSumUseCase(OpenpyxlFixedSumReader(), CsvFixedSumWriter())
    request = RunFixedSumRequest(
        file_paths=[str(input_path)],
        fecha="07/08/2026",
        hojas_a_sumar=1000,
        output_dir=str(tmp_path / "out"),
    )

    csv_paths = use_case.execute(request)

    assert len(csv_paths) == 1
    with open(csv_paths[0], encoding="utf-8") as f:
        content = f.read()
    assert "SERA;Activa en Cliente;500;07/08/2026;14;10;1500" in content
    assert "SERD;Activa en Cliente;1;07/08/2026;14;10;1" in content
