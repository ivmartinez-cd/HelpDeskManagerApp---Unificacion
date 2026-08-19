import sqlite3
from collections.abc import Callable
from ftplib import FTP
from pathlib import Path
from typing import cast

from src.modules.contadores.infrastructure.ftp.db3_merge import has_counter_data, is_sqlite3_valid
from src.modules.contadores.infrastructure.ftp.ftplib_db3_downloader import (
    _download_first_usable_day,
    _group_candidates_by_date,
)


class _FakeFtp:
    """Stub mínimo de ftplib.FTP: sirve contenido en memoria por nombre de archivo."""

    def __init__(self, contents: dict[str, bytes]) -> None:
        self._contents = contents

    def retrbinary(self, cmd: str, callback: Callable[[bytes], object]) -> None:
        remote_name = cmd.removeprefix("RETR ")
        callback(self._contents[remote_name])


def _make_db3(path: Path, *, with_data: bool) -> bytes:
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE counters (serialnumber TEXT, readdate TEXT, readvalue INTEGER, "
        "model TEXT, counterclass_id INTEGER)"
    )
    if with_data:
        conn.execute("INSERT INTO counters VALUES ('SN1', '2026-08-19', 100, 'ModeloX', 10)")
    conn.commit()
    conn.close()
    return path.read_bytes()


def test_group_candidates_agrupa_por_fecha_del_mas_reciente_al_mas_viejo() -> None:
    candidates = [
        "PrinterMonitorClient.db3.2026-08-18-09-00-00",
        "PrinterMonitorClient.db3.2026-08-19-09-00-00",
        "PrinterMonitorClient.db3.2026-08-19-15-00-00",
        "PrinterMonitorClient.db3.2026-08-20-17-14-06",
    ]

    groups = _group_candidates_by_date(candidates)

    assert groups == [
        ["PrinterMonitorClient.db3.2026-08-20-17-14-06"],
        [
            "PrinterMonitorClient.db3.2026-08-19-09-00-00",
            "PrinterMonitorClient.db3.2026-08-19-15-00-00",
        ],
        ["PrinterMonitorClient.db3.2026-08-18-09-00-00"],
    ]


def test_group_candidates_sin_fecha_detectable_queda_solo() -> None:
    candidates = ["sin_fecha.db3", "PrinterMonitorClient.db3.2026-08-19-09-00-00"]

    groups = _group_candidates_by_date(candidates)

    assert groups == [
        ["PrinterMonitorClient.db3.2026-08-19-09-00-00"],
        ["sin_fecha.db3"],
    ]


def test_has_counter_data_true_si_hay_al_menos_una_fila_valida(tmp_path: Path) -> None:
    path = tmp_path / "con_datos.db3"
    _make_db3(path, with_data=True)

    assert has_counter_data(str(path)) is True


def test_has_counter_data_false_si_la_tabla_esta_vacia(tmp_path: Path) -> None:
    path = tmp_path / "vacio.db3"
    _make_db3(path, with_data=False)

    assert has_counter_data(str(path)) is False


def test_has_counter_data_false_si_no_es_sqlite_valido(tmp_path: Path) -> None:
    path = tmp_path / "no_es_sqlite.db3"
    path.write_bytes(b"esto no es un sqlite")

    assert has_counter_data(str(path)) is False


def test_is_sqlite3_valid_true_para_sqlite_integro(tmp_path: Path) -> None:
    path = tmp_path / "valido.db3"
    _make_db3(path, with_data=True)

    assert is_sqlite3_valid(str(path)) is True


def test_is_sqlite3_valid_false_para_archivo_no_sqlite(tmp_path: Path) -> None:
    path = tmp_path / "invalido.db3"
    path.write_bytes(b"no sqlite" * 20)

    assert is_sqlite3_valid(str(path)) is False


def test_download_first_usable_day_hace_fallback_si_el_dia_mas_reciente_esta_vacio(
    tmp_path: Path,
) -> None:
    """Reproduce el caso real de DISTRINANDO: un DB3 con fecha futura (reloj
    desincronizado del equipo) llega vacío y no debe cortar el proceso —
    se avisa y se usa el día anterior, que sí tiene datos."""
    empty_name = "PrinterMonitorClient.db3.2026-08-20-17-14-06"
    empty_bytes = _make_db3(tmp_path / "src_empty.db3", with_data=False)

    data_name = "PrinterMonitorClient.db3.2026-08-19-11-09-43"
    data_bytes = _make_db3(tmp_path / "src_data.db3", with_data=True)

    ftp = _FakeFtp({empty_name: empty_bytes, data_name: data_bytes})
    day_groups = [[empty_name], [data_name]]
    dest_path = str(tmp_path / "dest.db3")

    result_path = _download_first_usable_day(cast(FTP, ftp), "DISTRINANDO", day_groups, dest_path)

    assert result_path == dest_path
    assert has_counter_data(result_path) is True


def test_download_first_usable_day_si_todos_los_dias_estan_vacios_devuelve_el_ultimo(
    tmp_path: Path,
) -> None:
    empty_name = "PrinterMonitorClient.db3.2026-08-20-17-14-06"
    empty_bytes = _make_db3(tmp_path / "src_empty.db3", with_data=False)

    ftp = _FakeFtp({empty_name: empty_bytes})
    day_groups = [[empty_name]]
    dest_path = str(tmp_path / "dest.db3")

    result_path = _download_first_usable_day(cast(FTP, ftp), "DISTRINANDO", day_groups, dest_path)

    assert result_path == dest_path
    assert has_counter_data(result_path) is False
