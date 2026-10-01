"""Lectura acotada de archivos subidos (auditoría de seguridad 2026-09-30): sin
tope, `await file.read()` cargaba en memoria lo que mandara el usuario. Los
archivos reales de la app (DB3, Excel de liquidaciones, PDFs de certificados)
rondan unos pocos MB; 50 MB deja margen holgado."""

from typing import ClassVar

from fastapi import UploadFile

from src.shared.domain.errors import ValidationError

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
_CHUNK = 1024 * 1024


class ArchivoDemasiadoGrandeError(ValidationError):
    http_status: ClassVar[int] = 413
    default_code: ClassVar[str] = "ARCHIVO_DEMASIADO_GRANDE"

    def __init__(self, max_bytes: int) -> None:
        super().__init__(f"El archivo supera el máximo de {max_bytes // (1024 * 1024)} MB")


async def leer_upload(file: UploadFile, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    partes: list[bytes] = []
    total = 0
    while parte := await file.read(_CHUNK):
        total += len(parte)
        if total > max_bytes:
            raise ArchivoDemasiadoGrandeError(max_bytes)
        partes.append(parte)
    return b"".join(partes)
