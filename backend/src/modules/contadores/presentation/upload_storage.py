import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from src.shared.infrastructure.config.settings import get_settings


async def save_upload(file: UploadFile) -> Path:
    """Guarda un archivo subido en un directorio temporal, con nombre único
    para no pisar cargas concurrentes. El caller es responsable de borrarlo
    (`Path.unlink(missing_ok=True)`) una vez procesado."""
    upload_dir = Path(get_settings().contadores_output_dir).parent / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = upload_dir / f"{stamp}_{uuid.uuid4().hex[:8]}_{file.filename}"
    destination.write_bytes(await file.read())
    return destination


def output_dir() -> str:
    return get_settings().contadores_output_dir
