"""Adaptador FTP que implementa el puerto FtpDb3Downloader usando ftplib.

Porta la lógica de HelpDeskManager-Web/backend/services/ftp_db3.py con las
siguientes adaptaciones:
- Se envuelve en la clase FtplibDb3Downloader (Adapter Pattern, ARCHITECTURE_GUIDE §5).
- Los errores de infraestructura se envuelven en ExternalServiceError (§6).
- Se usa ftp.close() y no ftp.quit() para evitar cuelgues de socket (mismo
  comentario del código original).
- No hay print() — los errores se propagan como excepciones.
"""
from __future__ import annotations

import contextlib
import fnmatch
import os
import re
import sqlite3
import tempfile
from ftplib import FTP, error_perm, error_proto, error_reply, error_temp
from pathlib import Path

from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.shared.domain.errors import ExternalServiceError


class FtplibDb3Downloader:
    """Implementación concreta del puerto FtpDb3Downloader con ftplib.

    Descarga el DB3 del día más reciente disponible en el directorio FTP
    del cliente. Si hay más de un archivo con la misma fecha, los fusiona
    en un único SQLite antes de retornar.
    """

    def download(
        self,
        client: FtpClient,
        *,
        dest_path: str,
        timeout: int = 8,
    ) -> str:
        try:
            return _download(client, dest_path=dest_path, timeout=timeout)
        except FileNotFoundError:
            raise
        except (error_perm, error_temp, error_proto, error_reply, OSError) as exc:
            raise ExternalServiceError(
                f"Error al conectar/descargar FTP para '{client.name}': {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Implementación interna (funciones libres, sin acceso a self)
# ---------------------------------------------------------------------------


def _download(client: FtpClient, *, dest_path: str, timeout: int) -> str:
    """Orquesta la conexión FTP, selección y descarga del archivo más reciente."""
    ftp = FTP(client.host, timeout=timeout)
    try:
        ftp.login(client.user, client.password)
        ftp.cwd(client.path)
        candidates = _list_remote_files(ftp, client.pattern)
        latest_files = _select_latest_day_files(candidates)

        if len(latest_files) == 1:
            _retrieve(ftp, latest_files[0], dest_path)
        else:
            dest_path = _download_and_merge(ftp, latest_files, dest_path)
    finally:
        # close() corta el socket sin handshake — evita cuelgues (ver ftp_db3.py original)
        with contextlib.suppress(Exception):
            ftp.close()

    return dest_path


def _list_remote_files(ftp: FTP, pattern: str) -> list[str]:
    """Lista archivos del directorio actual que coinciden con el patrón."""
    files = ftp.nlst()
    matches = sorted(f for f in files if fnmatch.fnmatch(f.lower(), pattern.lower()))
    if not matches:
        raise FileNotFoundError(
            f"No se encontraron archivos con patrón '{pattern}' en el servidor FTP."
        )
    return matches


def _select_latest_day_files(candidates: list[str]) -> list[str]:
    """De la lista ordenada, selecciona todos los archivos del día más reciente.

    Si el último candidato contiene una fecha (YYYY-MM-DD o YYYYMMDD),
    devuelve todos los que comparten esa misma fecha. Si no hay fecha
    detectable, devuelve solo el último candidato.
    """
    latest = candidates[-1]
    match = re.search(r"\d{4}[-/]?\d{2}[-/]?\d{2}", latest)
    if not match:
        return [latest]
    date_str = match.group(0)
    return [f for f in candidates if date_str in f] or [latest]


def _retrieve(ftp: FTP, remote_name: str, local_path: str) -> None:
    """Descarga un único archivo remoto a local_path."""
    with open(local_path, "wb") as f:
        ftp.retrbinary(f"RETR {remote_name}", f.write)


def _download_and_merge(ftp: FTP, remote_files: list[str], dest_path: str) -> str:
    """Descarga múltiples archivos y los fusiona en un único SQLite."""
    tmp_dir = tempfile.mkdtemp()
    local_paths: list[str] = []

    for remote in remote_files:
        local = os.path.join(tmp_dir, os.path.basename(remote))
        try:
            _retrieve(ftp, remote, local)
            if _is_sqlite3_valid(local):
                local_paths.append(local)
            else:
                _safe_remove(local)
        except Exception:
            _safe_remove(local)

    try:
        if not local_paths:
            raise ExternalServiceError("No se pudo descargar ningún archivo DB3 válido.")
        if len(local_paths) == 1:
            import shutil

            shutil.move(local_paths[0], dest_path)
            local_paths.clear()
        else:
            merge_db3_files(local_paths, dest_path)
    finally:
        for p in local_paths:
            _safe_remove(p)
        with contextlib.suppress(OSError):
            os.rmdir(tmp_dir)

    return dest_path


# ---------------------------------------------------------------------------
# Helpers de SQLite (portados de ftp_db3.py sin cambios semánticos)
# ---------------------------------------------------------------------------


def _is_sqlite3_valid(path: str) -> bool:
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
    except Exception:
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


def _get_pk_info(con: sqlite3.Connection, table: str) -> tuple[list[str], str | None, bool]:
    """Devuelve (columnas, nombre_pk, es_pk_int_simple)."""
    info = con.execute(f'PRAGMA table_info("{table}");').fetchall()
    cols = [r["name"] for r in info]
    pk_cols = [r for r in info if int(r["pk"] or 0) > 0]
    if len(pk_cols) == 1:
        pk_name = pk_cols[0]["name"]
        is_int = str(pk_cols[0]["type"] or "").upper() == "INTEGER"
        return cols, pk_name, is_int
    return cols, None, False


def _import_file(
    src_path: str,
    merged_con: sqlite3.Connection,
    table_names: list[str],
) -> None:
    src_con = sqlite3.connect(src_path)
    src_con.row_factory = sqlite3.Row
    try:
        for table in table_names:
            exists = src_con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists:
                continue

            cols, pk, is_int_pk = _get_pk_info(merged_con, table)

            if pk and is_int_pk and pk in cols:
                cols_no_pk = [c for c in cols if c != pk]
                if not cols_no_pk:
                    continue
                col_str = ", ".join(f'"{c}"' for c in cols_no_pk)
                rows = src_con.execute(f'SELECT {col_str} FROM "{table}";').fetchall()
                for row in rows:
                    merged_con.execute(
                        f'INSERT INTO "{table}" ({col_str}) VALUES ({",".join(["?"] * len(row))});',
                        tuple(row),
                    )
            else:
                col_str = ", ".join(f'"{c}"' for c in cols)
                rows = src_con.execute(f'SELECT {col_str} FROM "{table}";').fetchall()
                for row in rows:
                    placeholders = ",".join(["?"] * len(row))
                    merged_con.execute(
                        f'INSERT OR IGNORE INTO "{table}" ({col_str}) VALUES ({placeholders});',
                        tuple(row),
                    )
    finally:
        src_con.close()


def _safe_remove(path: str) -> None:
    with contextlib.suppress(OSError):
        os.remove(path)
