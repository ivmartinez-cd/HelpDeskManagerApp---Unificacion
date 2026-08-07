import csv
from pathlib import Path

from src.modules.contadores.domain.value_objects.estimation_zero_row import EstimationZeroRow

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


class CsvEstimationZeroWriter:
    def write(self, rows: list[EstimationZeroRow], *, output_dir: str, cliente: str) -> str:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{cliente}_Limpieza_Cero.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";", lineterminator="\r\n")
            writer.writerow(_FIELDNAMES)
            for r in rows:
                writer.writerow(
                    (
                        r.serie,
                        r.fecha,
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
