import csv
from pathlib import Path

from src.modules.contadores.domain.value_objects.db3_export_row import Db3ExportRow

_FIELDNAMES = (
    "SERIE",
    "FECHA",
    "TIPO",
    "CLASE_10",
    "CONTADOR_10",
    "CLASE_20",
    "CONTADOR_20",
    "MOTIVO",
    "OBSERVACION",
)


class CsvDb3Writer:
    """Mismo formato que la app vieja: `;` como separador, CRLF, UTF-8 sin BOM."""

    def write(self, rows: list[Db3ExportRow], *, output_dir: str, base_name: str) -> str:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{base_name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";", lineterminator="\r\n")
            writer.writerow(_FIELDNAMES)
            for r in rows:
                writer.writerow(
                    (
                        r.serie,
                        r.fecha.strftime("%d/%m/%Y"),
                        r.tipo,
                        r.clase_10,
                        r.contador_10,
                        r.clase_20,
                        r.contador_20,
                        "",
                        "",
                    )
                )
        return str(path)
