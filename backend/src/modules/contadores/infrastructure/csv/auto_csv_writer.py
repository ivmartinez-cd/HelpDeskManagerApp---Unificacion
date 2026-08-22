"""Salida `*_AutoCSV.csv` de los exports de contadores por API (SDS/HP Insight y
Epson ERS): mismo nombre de archivo y mismo formato (`;`, CRLF, UTF-8 sin BOM)
que generaba la app vieja, compartidos por ambos providers."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

AUTO_CSV_FIELDNAMES = (
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


@dataclass(frozen=True)
class AutoCsvTarget:
    """Dónde y con qué nombre se escribe el CSV:
    `<prefix>_<nombre_seguro>_<yyyymmdd>[_SumaColor]_AutoCSV.csv` dentro de `output_dir`."""

    prefix: str
    name: str
    max_date: str
    output_dir: str
    suma_color: bool = False

    def path(self) -> Path:
        date_str = self.max_date.split("T")[0].replace("-", "")
        safe_name = (
            "".join([c for c in self.name if c.isalnum() or c in (" ", "_")])
            .strip()
            .replace(" ", "_")
        )
        suffix = "_SumaColor" if self.suma_color else ""
        return Path(self.output_dir) / f"{self.prefix}_{safe_name}_{date_str}{suffix}_AutoCSV.csv"


def write_auto_csv(rows: list[dict[str, Any]], target: AutoCsvTarget) -> Path:
    """Escribe las filas en `target.path()` (creando el directorio) y devuelve la ruta."""
    output_path = target.path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUTO_CSV_FIELDNAMES, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return output_path
