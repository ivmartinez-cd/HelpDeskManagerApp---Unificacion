import os
import sqlite3
from datetime import date, datetime

from src.modules.contadores.domain.repositories.db3_file_reader import Db3ReadOutcome
from src.modules.contadores.domain.value_objects.db3_counter_row import Db3CounterRow

_REQUIRED_COLUMNS = {"serialnumber", "readdate", "readvalue", "model", "counterclass_id"}
_QUERY = "SELECT serialnumber, readdate, readvalue, model, counterclass_id FROM counters"


class Sqlite3Db3FileReader:
    """Lee la tabla `counters` de uno o más DB3 (SQLite) — mismo esquema que
    la app vieja verificó en vivo el 2026-08-07."""

    def read(self, file_paths: list[str]) -> Db3ReadOutcome:
        rows: list[Db3CounterRow] = []
        warnings: list[str] = []
        for path in file_paths:
            file_rows, warning = _read_one_file(path)
            rows.extend(file_rows)
            if warning:
                warnings.append(warning)
        return Db3ReadOutcome(rows=rows, warnings=warnings)


def _read_one_file(path: str) -> tuple[list[Db3CounterRow], str | None]:
    filename = os.path.basename(path)
    if not os.path.isfile(path):
        return [], f"Archivo no encontrado: {filename}"
    try:
        conn = sqlite3.connect(path)
        try:
            if not _has_expected_structure(conn):
                return [], f"Estructura inesperada en DB: {filename}"
            db_rows = conn.execute(_QUERY).fetchall()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return [], f"Error procesando {filename}: {exc}"

    parsed = [r for r in (_parse_row(row) for row in db_rows) if r is not None]
    if not parsed:
        return [], f"Sin datos válidos en: {filename}"
    return parsed, None


def _has_expected_structure(conn: sqlite3.Connection) -> bool:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(counters)")}
    return _REQUIRED_COLUMNS.issubset(cols)


def _parse_row(row: tuple[object, ...]) -> Db3CounterRow | None:
    serial, read_date_raw, read_value, model, counter_class_id = row
    read_date = _parse_date(read_date_raw)
    if read_date is None or read_value is None or counter_class_id is None:
        return None
    return Db3CounterRow(
        serial_number=str(serial),
        read_date=read_date,
        read_value=int(read_value),  # type: ignore[call-overload]
        model=str(model or ""),
        counter_class_id=int(counter_class_id),  # type: ignore[call-overload]
    )


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None
