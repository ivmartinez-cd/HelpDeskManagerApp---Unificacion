import csv
from collections.abc import Sequence

from src.modules.contadores.domain.errors import MissingColumnError
from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)

_SERIE_ALIASES = ("SERIE", "Nro_serie")
_CONTADOR_ALIASES = ("CONTADOR", "ImpreContadorAnterior")


class CsvFaltaContadorReader:
    """Lee el CSV export de SIGES (delimitador auto-detectado, BOM tolerado)
    que alimenta Estimación en 0 — mismo formato que `counters_tools.py`."""

    def read(self, file_path: str) -> list[FaltaContadorSourceRow]:
        with open(file_path, encoding="utf-8-sig", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = _sniff_delimiter(sample)
            reader = csv.DictReader(f, delimiter=delimiter)
            header = reader.fieldnames or []
            serie_col = _find_column(header, _SERIE_ALIASES)
            contador_col = _find_column(header, _CONTADOR_ALIASES)
            tipo_col = _find_column(header, ("Tipo",))
            nombre_clase_col = _find_optional_column(header, ("NombreClase",))
            return [
                _parse_row(row, tipo_col, serie_col, contador_col, nombre_clase_col)
                for row in reader
            ]


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,").delimiter
    except csv.Error:
        return ","


def _find_column(header: Sequence[str], aliases: tuple[str, ...]) -> str:
    stripped = {h.strip(): h for h in header}
    for alias in aliases:
        if alias in stripped:
            return stripped[alias]
    raise MissingColumnError(aliases[0])


def _find_optional_column(header: Sequence[str], aliases: tuple[str, ...]) -> str | None:
    stripped = {h.strip(): h for h in header}
    for alias in aliases:
        if alias in stripped:
            return stripped[alias]
    return None


def _parse_row(
    row: dict[str, str],
    tipo_col: str,
    serie_col: str,
    contador_col: str,
    nombre_clase_col: str | None,
) -> FaltaContadorSourceRow:
    # Igual que `counters_tools.py`: cuando la columna NombreClase existe pero
    # el valor de esta fila viene vacío/None, se trata como "no Color" (va a
    # CLASE_10), no como "columna ausente" (que deja ambas columnas vacías).
    # Por eso acá nunca devolvemos None si la columna existe en el header.
    nombre_clase = (row.get(nombre_clase_col) or "").strip() if nombre_clase_col else None
    return FaltaContadorSourceRow(
        tipo=row.get(tipo_col, ""),
        serie=row.get(serie_col, ""),
        contador=int(float(row.get(contador_col) or 0)),
        nombre_clase=nombre_clase,
    )
