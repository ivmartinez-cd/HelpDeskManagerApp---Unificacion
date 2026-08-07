import contextlib
import os
import re
import tempfile
import uuid

from src.modules.contadores.application.dtos.download_ftp_db3_request import DownloadFtpDb3Request
from src.modules.contadores.application.dtos.download_ftp_db3_result import DownloadFtpDb3Result
from src.modules.contadores.application.dtos.run_db3_export_request import RunDb3ExportRequest
from src.modules.contadores.application.use_cases.run_db3_export import RunDb3ExportUseCase
from src.modules.contadores.domain.errors import FtpClientNotFoundError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository
from src.modules.contadores.domain.repositories.ftp_db3_downloader import FtpDb3Downloader

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]")


class DownloadAndProcessFtpDb3UseCase:
    """Descarga el DB3 más reciente vía FTP y lo procesa como si fuera un
    upload manual (reutiliza RunDb3ExportUseCase).

    Flujo:
    1. Obtiene el FtpClient de la DB (404 si no existe).
    2. Descarga el DB3 a un temporal.
    3. Delega el procesamiento a RunDb3ExportUseCase.
    4. Borra el temporal (incluso si el procesamiento falla).
    """

    def __init__(
        self,
        repo: FtpClientRepository,
        downloader: FtpDb3Downloader,
        db3_use_case: RunDb3ExportUseCase,
    ) -> None:
        self._repo = repo
        self._downloader = downloader
        self._db3_use_case = db3_use_case

    async def execute(self, request: DownloadFtpDb3Request) -> DownloadFtpDb3Result:
        client = await self._repo.get_by_id(uuid.UUID(request.client_id))
        if client is None:
            raise FtpClientNotFoundError()

        safe_name = _SAFE_NAME_RE.sub("_", client.name)
        fd, dest_path = tempfile.mkstemp(suffix=".db3", prefix=f"{safe_name}_FTP_")
        os.close(fd)

        try:
            remote_filename = os.path.basename(
                self._downloader.download(
                    client,
                    dest_path=dest_path,
                    timeout=request.timeout,
                )
            )

            export_request = RunDb3ExportRequest(
                file_paths=[dest_path],
                base_name=f"{safe_name}_FTP",
                output_dir=request.output_dir,
                fecha_maxima=request.fecha_maxima,
            )
            export_result = self._db3_use_case.execute(export_request)
        finally:
            with contextlib.suppress(OSError):
                os.remove(dest_path)

        return DownloadFtpDb3Result(
            csv_path=export_result.csv_path,
            client_name=client.name,
            remote_filename=remote_filename,
            row_count=export_result.row_count,
            warnings=export_result.warnings,
        )
