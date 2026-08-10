from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from src.modules.contadores.application.dtos.download_ftp_db3_result import DownloadFtpDb3Result
from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientResult


class FtpClientIn(BaseModel):
    """Payload para crear o actualizar un cliente FTP.

    `password` es obligatorio al crear (validado en el router, no acá,
    porque este mismo schema se reusa para el PUT) — al editar, omitirlo
    conserva la contraseña actual: `FtpClientOut` nunca la devuelve, así que
    no hay forma de precargarla y reenviarla tal cual."""

    name: str = Field(..., min_length=1, description="Nombre identificador del cliente")
    host: str = Field(..., min_length=1, description="Hostname o IP del servidor FTP")
    user: str = Field(..., min_length=1, description="Usuario FTP")
    password: str | None = Field(
        None, min_length=1, description="Contraseña FTP (obligatoria al crear)"
    )
    path: str = Field("/", description="Directorio remoto a navegar (debe comenzar con '/')")
    pattern: str = Field(
        "PrinterMonitorClient.db3.*", description="Patrón glob para filtrar archivos"
    )


class FtpClientOut(BaseModel):
    """Representación de un cliente FTP devuelta por la API (sin password)."""

    id: str
    name: str
    host: str
    user: str
    path: str
    pattern: str

    @classmethod
    def from_result(cls, result: FtpClientResult) -> FtpClientOut:
        return cls(
            id=result.id,
            name=result.name,
            host=result.host,
            user=result.user,
            path=result.path,
            pattern=result.pattern,
        )


class ProcessFtpClientRequest(BaseModel):
    """Payload para disparar descarga+procesamiento de un cliente FTP."""

    fecha_maxima: date | None = Field(
        None, description="Fecha máxima de lectura a incluir en el CSV (opcional)"
    )


class ProcessFtpClientResponse(BaseModel):
    """Resultado del proceso FTP+DB3→CSV."""

    client_name: str
    remote_filename: str
    csv_filename: str
    db3_filename: str
    row_count: int
    warnings: list[str]

    @classmethod
    def from_result(cls, result: DownloadFtpDb3Result) -> ProcessFtpClientResponse:
        return cls(
            client_name=result.client_name,
            remote_filename=result.remote_filename,
            csv_filename=Path(result.csv_path).name,
            db3_filename=Path(result.db3_path).name,
            row_count=result.row_count,
            warnings=result.warnings,
        )
