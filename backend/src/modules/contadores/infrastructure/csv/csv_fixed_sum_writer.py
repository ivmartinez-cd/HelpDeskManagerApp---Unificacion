import csv
from pathlib import Path

from src.modules.contadores.domain.value_objects.fixed_sum_result_row import FixedSumResultRow

_FIELDNAMES = ("SERIE", "Estado", "Cdor Actual", "FECHA", "TIPO", "CLASE", "CONTADOR")


class CsvFixedSumWriter:
    def write(self, rows: list[FixedSumResultRow], *, output_dir: str, base_name: str) -> str:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{base_name}_SumaFija.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(_FIELDNAMES)
            for r in rows:
                writer.writerow(
                    (
                        r.serie,
                        r.estado,
                        r.contador_actual,
                        r.fecha,
                        r.tipo,
                        r.clase,
                        r.contador,
                    )
                )
        return str(path)
