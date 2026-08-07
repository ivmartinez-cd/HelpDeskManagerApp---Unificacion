from typing import Protocol

from src.modules.contadores.domain.value_objects.db3_export_row import Db3ExportRow


class Db3CsvWriter(Protocol):
    def write(self, rows: list[Db3ExportRow], *, output_dir: str, base_name: str) -> str: ...
