from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DownloadFtpDb3Result:
    """Output del use case de descarga y procesamiento de DB3 vía FTP."""

    csv_path: str
    client_name: str
    remote_filename: str
    row_count: int
    warnings: list[str] = field(default_factory=list)
