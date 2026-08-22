import csv
import sqlite3

from src.modules.contadores.application.dtos.run_db3_export_request import RunDb3ExportRequest
from src.modules.contadores.application.use_cases.run_db3_export import RunDb3ExportUseCase
from src.modules.contadores.infrastructure.csv.csv_db3_writer import CsvDb3Writer
from src.modules.contadores.infrastructure.sqlite.sqlite3_db3_file_reader import (
    Sqlite3Db3FileReader,
)


def _write_db3(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE counters "
        "(serialnumber TEXT, readdate TEXT, readvalue INTEGER, model TEXT, counterclass_id INTEGER)"
    )
    conn.executemany(
        "INSERT INTO counters VALUES (?,?,?,?,?)",
        [
            ("SER001", "2026-08-05 10:00:00", 1000, "ModeloNormal", 10),
            ("SER001", "2026-08-05 10:00:00", 200, "ModeloNormal", 20),
            ("SER002", "2026-08-05 10:00:00", 5000, "C4010ND", 40),
        ],
    )
    conn.commit()
    conn.close()


def test_end_to_end_matches_live_verified_legacy_output(tmp_path) -> None:
    db3_path = tmp_path / "muestra.db3"
    _write_db3(str(db3_path))

    use_case = RunDb3ExportUseCase(Sqlite3Db3FileReader(), CsvDb3Writer())
    request = RunDb3ExportRequest(
        file_paths=[str(db3_path)], base_name="salida", output_dir=str(tmp_path / "out")
    )

    result = use_case.execute(request)

    assert result.row_count == 2
    assert result.warnings == []

    with open(result.csv_path, encoding="utf-8", newline="") as f:
        rows = {r["SERIE"]: r for r in csv.DictReader(f, delimiter=";")}

    assert rows["SER001"]["CLASE_10"] == "10" and rows["SER001"]["CONTADOR_10"] == "1000"
    assert rows["SER001"]["CLASE_20"] == "20" and rows["SER001"]["CONTADOR_20"] == "200"
    # Modelo especial (C4010ND) que solo reporta clase 40: el total va como
    # COLOR en la primera columna y NO se duplica en la 20 (commit 3eb8a23,
    # 2026-08-19: la app vieja lo duplicaba y SiGes rechazaba el mono inventado).
    assert rows["SER002"]["CLASE_10"] == "20" and rows["SER002"]["CONTADOR_10"] == "5000"
    assert rows["SER002"]["CLASE_20"] == "" and rows["SER002"]["CONTADOR_20"] == "0"


def test_missing_file_is_reported_as_warning_not_a_crash(tmp_path) -> None:
    db3_path = tmp_path / "muestra.db3"
    _write_db3(str(db3_path))

    use_case = RunDb3ExportUseCase(Sqlite3Db3FileReader(), CsvDb3Writer())
    request = RunDb3ExportRequest(
        file_paths=[str(db3_path), str(tmp_path / "no_existe.db3")],
        base_name="salida",
        output_dir=str(tmp_path / "out"),
    )

    result = use_case.execute(request)

    assert result.row_count == 2
    assert len(result.warnings) == 1
    assert "no_existe.db3" in result.warnings[0]
