"""merge_db3_files: fusión de varios SQLite DB3 del mismo día sin ATTACH."""

import sqlite3
from pathlib import Path

import pytest

from src.modules.contadores.infrastructure.ftp.db3_merge import merge_db3_files


def _make_db3(path: Path, *, counters: list[tuple[str, int]], with_tags: bool) -> str:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE counters (id INTEGER PRIMARY KEY, serialnumber TEXT, "
        "readvalue INTEGER)"
    )
    conn.executemany(
        "INSERT INTO counters (serialnumber, readvalue) VALUES (?, ?)", counters
    )
    # PK compuesta: se copia con INSERT OR IGNORE (los duplicados se descartan).
    conn.execute("CREATE TABLE tags (k TEXT, v TEXT, PRIMARY KEY (k, v))")
    conn.executemany("INSERT INTO tags VALUES (?, ?)", [("a", "1"), ("b", "2")])
    if with_tags:
        conn.execute("CREATE TABLE only_in_base (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    return str(path)


def _fetch(path: str, sql: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(path)
    try:
        return [tuple(r) for r in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def test_merge_db3_files_copia_filas_regenera_pk_integer_e_ignora_duplicados(
    tmp_path: Path,
) -> None:
    first = _make_db3(tmp_path / "a.db3", counters=[("SN1", 10), ("SN2", 20)], with_tags=False)
    second = _make_db3(tmp_path / "b.db3", counters=[("SN3", 30)], with_tags=True)

    merged = merge_db3_files([first, second], str(tmp_path / "out" / "merged.db3"))

    assert merged.endswith("merged.db3")
    # La PK INTEGER simple se omite al insertar: los ids se regeneran y no chocan.
    assert _fetch(merged, "SELECT id, serialnumber, readvalue FROM counters ORDER BY id") == [
        (1, "SN1", 10),
        (2, "SN2", 20),
        (3, "SN3", 30),
    ]
    # PK compuesta: las mismas filas en ambos archivos quedan una sola vez.
    assert _fetch(merged, "SELECT k, v FROM tags ORDER BY k") == [("a", "1"), ("b", "2")]
    # Tabla presente solo en el schema base: se crea y el archivo que no la tiene se saltea.
    assert _fetch(merged, "SELECT COUNT(*) FROM only_in_base") == [(0,)]


def test_merge_db3_files_con_un_solo_archivo_lo_devuelve_tal_cual(tmp_path: Path) -> None:
    only = _make_db3(tmp_path / "a.db3", counters=[("SN1", 10)], with_tags=False)
    assert merge_db3_files([only], str(tmp_path / "merged.db3")) == only


def test_merge_db3_files_sin_archivos_falla() -> None:
    with pytest.raises(ValueError, match="No hay archivos"):
        merge_db3_files([], "x.db3")


def test_merge_db3_files_rechaza_identificadores_inseguros(tmp_path: Path) -> None:
    bad = tmp_path / "bad.db3"
    conn = sqlite3.connect(bad)
    conn.execute('CREATE TABLE "t;x" (id INTEGER PRIMARY KEY, v TEXT)')
    conn.commit()
    conn.close()
    other = _make_db3(tmp_path / "a.db3", counters=[("SN1", 10)], with_tags=False)

    with pytest.raises(ValueError, match="Identificador SQLite inesperado"):
        merge_db3_files([other, str(bad)], str(tmp_path / "merged.db3"))
