from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DownloadFtpDb3Request:
    """Input para descargar y procesar el DB3 de un cliente FTP."""

    client_id: str
    output_dir: str
    fecha_maxima: date | None = None
    timeout: int = 8
