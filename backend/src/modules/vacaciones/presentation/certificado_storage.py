"""Storage en disco de los certificados/órdenes médicas adjuntas a una
`Ausencia`.

Mismo patrón que `analisis_log_hp/presentation/cpmd_storage.py`: directorio
bajo `var/` dentro del bind-mount del backend (persiste en el host). El
archivo es permanente y se sirve por `ausencia_id`, nunca por nombre de
archivo crudo, así que no hay riesgo de path traversal en el endpoint de
lectura.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from src.shared.domain.errors import ValidationError
from src.shared.infrastructure.config.settings import get_settings

_EXTENSIONES_PERMITIDAS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


def certificados_dir() -> Path:
    path = Path(get_settings().vacaciones_certificados_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_certificado(file: UploadFile) -> str:
    """Guarda el certificado (PDF o foto/escaneo) con un nombre único y
    devuelve el nombre de archivo (no el path)."""
    extension = _EXTENSIONES_PERMITIDAS.get(file.content_type or "")
    if extension is None:
        raise ValidationError("El certificado debe ser un PDF, JPG o PNG")
    filename = f"{uuid.uuid4().hex}{extension}"
    (certificados_dir() / filename).write_bytes(await file.read())
    return filename
