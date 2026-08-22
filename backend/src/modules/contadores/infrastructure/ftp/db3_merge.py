"""Operaciones de bajo nivel sobre archivos DB3 (SQLite) descargados por FTP:
validación de integridad, chequeo de datos utilizables y fusión de varios
archivos del mismo día en un único SQLite. Sin dependencia de ftplib —
separado de ftplib_db3_downloader.py por tamaño de archivo (ARCHITECTURE_GUIDE §4)."""
from __future__ import annotations

import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_REQUIRED_COUNTER_COLUMNS = {"readdate", "readvalue", "counterclass_id"}


def is_sqlite3_valid(path: str) -> bool:
    """Verifica que un archivo es un SQLite3 válido e íntegro."""
    try:
        if not os.path.isfile(path) or os.path.getsize(path) < 100:
            return False
        with open(path, "rb") as f:
            if not f.read(16).startswith(b"SQLite format 3\x00"):
                return False
        conn = sqlite3.connect(path)
        result = conn.execute("PRAGMA integrity_check(1);").fetchone()
        conn.close()
        return bool(result == ("ok",))
    except Exception as exc:
        logger.debug(
            "Archivo DB3 descartado por no ser un SQLite3 válido",
            extra={"path": path},
            exc_info=exc,
        )
        return False


def has_counter_data(path: str) -> bool:
    """True si el DB3 tiene al menos una fila de `counters` con las columnas
    mínimas no nulas (mismo criterio de validez que usa Sqlite3Db3FileReader
    para descartar filas — ver infrastructure/sqlite/sqlite3_db3_file_reader.py).
    Un DB3 estructuralmente válido pero sin ninguna lectura real (ej: el
    archivo con fecha futura de un equipo con el reloj desincronizado)
    devuelve False acá."""
    try:
        conn = sqlite3.connect(path)
        try:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(counters)")}
            if not _REQUIRED_COUNTER_COLUMNS.issubset(cols):
                return False
            row = conn.execute(
                "SELECT 1 FROM counters WHERE readdate IS NOT NULL "
                "AND readvalue IS NOT NULL AND counterclass_id IS NOT NULL LIMIT 1"
            ).fetchone()
            return row is not None
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def merge_db3_files(local_files: list[str], merged_path: str) -> str:
    """Fusiona múltiples SQLite DB3 en uno solo SIN usar ATTACH DATABASE.

    Estrategia (igual a la app vieja):
    - Copia schema desde el último archivo (base_db).
    - Copia filas tabla por tabla.
    - Si hay PK INTEGER simple, inserta sin esa columna (evita conflictos).
    - Usa INSERT OR IGNORE para PKs compuestas o no-integer.
    """
    if not local_files:
        raise ValueError("No hay archivos para fusionar.")
    if len(local_files) == 1:
        return local_files[0]

    base_db = local_files[-1]
    Path(merged_path).parent.mkdir(parents=True, exist_ok=True)

    schema_rows = _read_schema(base_db)
    merged_con = sqlite3.connect(merged_path)
    merged_con.row_factory = sqlite3.Row

    try:
        _create_schema(merged_con, schema_rows)
        table_names = _get_table_names(merged_con)

        merged_con.execute("PRAGMA foreign_keys=OFF;")
        merged_con.execute("BEGIN;")
        for src in local_files:
            _import_file(src, merged_con, table_names)
        merged_con.execute("COMMIT;")
    except Exception:
        merged_con.rollback()
        raise
    finally:
        merged_con.close()

    return merged_path


def _read_schema(db_path: str) -> list[sqlite3.Row]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
            ORDER BY
              CASE type
                WHEN 'table'   THEN 1
                WHEN 'view'    THEN 2
                WHEN 'index'   THEN 3
                WHEN 'trigger' THEN 4
                ELSE 99
              END, name
            """
        ).fetchall()
    finally:
        con.close()


def _create_schema(con: sqlite3.Connection, schema_rows: list[sqlite3.Row]) -> None:
    con.execute("PRAGMA foreign_keys=OFF;")
    con.execute("BEGIN;")
    for row in schema_rows:
        sql = (row["sql"] or "").strip()
        if sql:
            con.execute(sql)
    con.execute("COMMIT;")


def _get_table_names(con: sqlite3.Connection) -> list[str]:
    rows = con.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


_IDENT = re.compile(r"^[A-Za-z0-9_]+$")


def _ident(nombre: str) -> str:
    """Nombre de tabla/columna seguro para interpolar entre comillas dobles.

    Los nombres salen del `sqlite_master` del .db3 que llega por FTP (archivo
    externo, no input de usuario); aun así §8 prohíbe concatenar identificadores
    sin validar: un nombre con `"` o `;` rompería la consulta armada."""
    if not _IDENT.match(nombre):
        raise ValueError(f"Identificador SQLite inesperado en el .db3: {nombre!r}")
    return nombre


def _get_pk_info(con: sqlite3.Connection, table: str) -> tuple[list[str], str | None, bool]:
    """Devuelve (columnas, nombre_pk, es_pk_int_simple)."""
    info = con.execute(f'PRAGMA table_info("{_ident(table)}");').fetchall()
    cols = [_ident(r["name"]) for r in info]
    pk_cols = [r for r in info if int(r["pk"] or 0) > 0]
    if len(pk_cols) == 1:
        pk_name = pk_cols[0]["name"]
        is_int = str(pk_cols[0]["type"] or "").upper() == "INTEGER"
        return cols, pk_name, is_int
    return cols, None, False


@dataclass(frozen=True)
class _CopyPlan:
    """Cómo copiar una tabla al merge: qué columnas leer y con qué INSERT escribirlas."""

    table: str
    columns: list[str]
    insert_verb: str  # "INSERT" | "INSERT OR IGNORE"


def _import_file(
    src_path: str,
    merged_con: sqlite3.Connection,
    table_names: list[str],
) -> None:
    src_con = sqlite3.connect(src_path)
    src_con.row_factory = sqlite3.Row
    try:
        for table in table_names:
            if not _table_exists(src_con, table):
                continue
            plan = _plan_copy(merged_con, table)
            if plan is not None:
                _copy_rows(src_con, merged_con, plan)
    finally:
        src_con.close()


def _table_exists(con: sqlite3.Connection, table: str) -> bool:
    exists = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return exists is not None


def _plan_copy(merged_con: sqlite3.Connection, table: str) -> _CopyPlan | None:
    """Con PK INTEGER simple se inserta sin esa columna (se regenera y no choca);
    con PK compuesta o no-integer, todas las columnas con INSERT OR IGNORE.
    None si la tabla no tiene nada que copiar fuera de su PK."""
    cols, pk, is_int_pk = _get_pk_info(merged_con, table)
    if not (pk and is_int_pk and pk in cols):
        return _CopyPlan(table, cols, "INSERT OR IGNORE")
    cols_no_pk = [c for c in cols if c != pk]
    if not cols_no_pk:
        return None
    return _CopyPlan(table, cols_no_pk, "INSERT")


def _copy_rows(
    src_con: sqlite3.Connection, merged_con: sqlite3.Connection, plan: _CopyPlan
) -> None:
    col_str = ", ".join(f'"{c}"' for c in plan.columns)
    rows = src_con.execute(f'SELECT {col_str} FROM "{plan.table}";').fetchall()
    for row in rows:
        placeholders = ",".join(["?"] * len(row))
        merged_con.execute(
            f'{plan.insert_verb} INTO "{plan.table}" ({col_str}) VALUES ({placeholders});',
            tuple(row),
        )
