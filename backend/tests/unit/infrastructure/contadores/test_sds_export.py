"""Armado de filas del CSV SDS (sds_export) y destino `*_AutoCSV.csv` compartido."""

from datetime import datetime
from pathlib import Path

from src.modules.contadores.infrastructure.csv.auto_csv_writer import (
    AutoCsvTarget,
    write_auto_csv,
)
from src.modules.contadores.infrastructure.sds.sds_export import (
    MeterRowContext,
    build_meter_rows,
)


def _ctx(*, min_dt: datetime | None, suma_color: bool = False) -> MeterRowContext:
    return MeterRowContext(
        customer_id="c1", serial_map={10: "S10"}, min_dt=min_dt, suma_color=suma_color
    )


def test_build_meter_rows_usa_reading_datetime_como_fallback_y_no_filtra_sin_min_dt() -> None:
    meters = [
        {"deviceId": 10, "readingDateTime": "2020-01-05T08:00:00", "monoPages": 3},
        {"readingDate": "2026-08-01", "monoPages": 1},  # sin deviceId: SERIE vacía
    ]

    rows = build_meter_rows(meters, _ctx(min_dt=None))

    assert [(r["SERIE"], r["FECHA"], r["CONTADOR_10"]) for r in rows] == [
        ("S10", "05/01/2020", 3),
        ("", "01/08/2026", 1),
    ]
    # Sin color: CLASE_20 vacía y CONTADOR_20 en 0.
    assert rows[0]["CLASE_20"] == "" and rows[0]["CONTADOR_20"] == 0


def test_build_meter_rows_suma_color_solo_aplica_a_equipos_con_color() -> None:
    meters = [
        {"deviceId": 10, "readingDate": "2026-08-01", "engineCycles": 50, "monoPages": 40,
         "colourPages": 10},
        {"deviceId": 11, "readingDate": "2026-08-01", "engineCycles": 9, "monoPages": 9},
    ]

    rows = build_meter_rows(meters, _ctx(min_dt=datetime(2026, 7, 15), suma_color=True))

    assert (rows[0]["CLASE_10"], rows[0]["CONTADOR_10"]) == (20, 50)
    assert (rows[1]["CLASE_10"], rows[1]["CONTADOR_10"], rows[1]["CONTADOR_20"]) == (10, 9, 0)


def test_auto_csv_target_sanea_el_nombre_y_write_devuelve_la_ruta(tmp_path: Path) -> None:
    target = AutoCsvTarget(
        prefix="EPSON",
        name="Cliente/Raro  S.A.",
        max_date="2026-08-14T10:00:00",
        output_dir=str(tmp_path / "sub"),
        suma_color=True,
    )

    ruta = write_auto_csv([], target)

    assert ruta == tmp_path / "sub" / "EPSON_ClienteRaro__SA_20260814_SumaColor_AutoCSV.csv"
    assert ruta.read_text(encoding="utf-8").startswith("SERIE;FECHA;TIPO;CLASE_10;CONTADOR_10")
