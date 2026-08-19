"""Adaptador FTP que implementa el puerto FtpDb3Downloader usando ftplib.

Porta la lógica de HelpDeskManager-Web/backend/services/ftp_db3.py con las
siguientes adaptaciones:
- Se envuelve en la clase FtplibDb3Downloader (Adapter Pattern, ARCHITECTURE_GUIDE §5).
- Los errores de infraestructura se envuelven en ExternalServiceError (§6).
- Se usa ftp.close() y no ftp.quit() para evitar cuelgues de socket (mismo
  comentario del código original).
- No hay print() — los errores se propagan como excepciones.
- La fusión de DB3 y las validaciones de contenido SQLite viven en
  db3_merge.py (separado por tamaño de archivo, ARCHITECTURE_GUIDE §4).
"""
from __future__ import annotations

import contextlib
import fnmatch
import logging
import os
import re
import shutil
import tempfile
from ftplib import FTP, error_perm, error_proto, error_reply, error_temp

from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.infrastructure.ftp.db3_merge import (
    has_counter_data,
    is_sqlite3_valid,
    merge_db3_files,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class FtplibDb3Downloader:
    """Implementación concreta del puerto FtpDb3Downloader con ftplib.

    Descarga el DB3 del día más reciente disponible en el directorio FTP
    del cliente que tenga datos válidos. Si el día más reciente resulta sin
    datos (ej: un archivo con fecha futura por reloj desincronizado del
    equipo), se avisa por log y se prueba con el día anterior. Si hay más
    de un archivo con la misma fecha, los fusiona en un único SQLite antes
    de retornar.
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
    """Orquesta la conexión FTP, selección y descarga del día más reciente
    con datos válidos."""
    ftp = FTP(client.host, timeout=timeout)
    try:
        ftp.login(client.user, client.password)
        ftp.cwd(client.path)
        candidates = _list_remote_files(ftp, client.pattern)
        day_groups = _group_candidates_by_date(candidates)
        return _download_first_usable_day(ftp, client.name, day_groups, dest_path)
    finally:
        # close() corta el socket sin handshake — evita cuelgues (ver ftp_db3.py original)
        with contextlib.suppress(Exception):
            ftp.close()


def _list_remote_files(ftp: FTP, pattern: str) -> list[str]:
    """Lista archivos del directorio actual que coinciden con el patrón,
    ordenados cronológicamente (el nombre embebe fecha-hora ordenable)."""
    files = ftp.nlst()
    matches = sorted(f for f in files if fnmatch.fnmatch(f.lower(), pattern.lower()))
    if not matches:
        raise FileNotFoundError(
            f"No se encontraron archivos con patrón '{pattern}' en el servidor FTP."
        )
    return matches


def _group_candidates_by_date(candidates: list[str]) -> list[list[str]]:
    """Agrupa los candidatos (ya ordenados cronológicamente) por fecha
    detectada en el nombre (YYYY-MM-DD o YYYYMMDD), del día más reciente al
    más viejo. Un candidato sin fecha detectable queda solo en su propio
    grupo."""
    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for f in candidates:
        match = re.search(r"\d{4}[-/]?\d{2}[-/]?\d{2}", f)
        key = match.group(0) if match else f
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(f)
    return [groups[key] for key in reversed(order)]


def _download_first_usable_day(
    ftp: FTP, client_name: str, day_groups: list[list[str]], dest_path: str
) -> str:
    """Descarga el día más reciente; si resulta sin datos válidos, avisa por
    log y prueba con el día anterior. Si ninguno tiene datos, devuelve
    igual el último probado para que el flujo normal (RunDb3ExportUseCase)
    reporte el error de "sin datos" como siempre lo hizo."""
    result_path = dest_path
    for day_files in day_groups:
        result_path = _download_day(ftp, day_files, dest_path)
        if has_counter_data(result_path):
            return result_path
        logger.warning(
            "DB3 del día más reciente sin datos válidos, se prueba el día anterior",
            extra={"client": client_name, "files": day_files},
        )
    return result_path


def _download_day(ftp: FTP, day_files: list[str], dest_path: str) -> str:
    """Descarga los archivos de un mismo día a dest_path (fusionándolos si
    hay más de uno). Limpia cualquier resto de un día anterior probado."""
    with contextlib.suppress(OSError):
        os.remove(dest_path)
    if len(day_files) == 1:
        _retrieve(ftp, day_files[0], dest_path)
        return dest_path
    return _download_and_merge(ftp, day_files, dest_path)


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
            if is_sqlite3_valid(local):
                local_paths.append(local)
            else:
                _safe_remove(local)
        except Exception as exc:
            logger.warning(
                "No se pudo descargar/validar un archivo DB3 del FTP, se descarta y sigue",
                extra={"remote_file": remote},
                exc_info=exc,
            )
            _safe_remove(local)

    try:
        if not local_paths:
            raise ExternalServiceError("No se pudo descargar ningún archivo DB3 válido.")
        if len(local_paths) == 1:
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


def _safe_remove(path: str) -> None:
    with contextlib.suppress(OSError):
        os.remove(path)
