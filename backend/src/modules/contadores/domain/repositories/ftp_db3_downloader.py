from typing import Protocol

from src.modules.contadores.domain.entities.ftp_client import FtpClient


class FtpDb3Downloader(Protocol):
    """Puerto de dominio para descargar el DB3 más reciente del servidor FTP
    de un cliente. La implementación concreta vive en infrastructure/ftp/.

    Retorna el path local del archivo descargado (o fusionado si hay varios
    archivos del mismo día). El llamador es responsable de borrar el archivo
    temporal una vez procesado.
    """

    def download(
        self,
        client: FtpClient,
        *,
        dest_path: str,
        timeout: int = 8,
    ) -> str:
        """Descarga el DB3 más reciente y lo escribe en `dest_path`.

        Args:
            client: Configuración de acceso FTP del cliente.
            dest_path: Path local donde se escribirá el archivo descargado.
            timeout: Segundos de timeout para la conexión FTP.

        Returns:
            Path local del archivo escrito (igual a `dest_path`).

        Raises:
            FileNotFoundError: Si no hay archivos que coincidan con el patrón.
            ExternalServiceError: Si la conexión o descarga falla.
        """
        ...
