"""Fotos adjuntas a los reportes. Mismo patrón que
`vacaciones/presentation/certificado_storage.py`: directorio bajo `var/` del
bind-mount del backend, nombre único generado acá (nunca el del usuario). La
app no las sirve: las lee el servidor MCP directo del disco del host."""

import uuid
from pathlib import Path

from fastapi import UploadFile

from src.shared.domain.errors import ValidationError
from src.shared.presentation.uploads import leer_upload

FOTOS_DIR = Path("var/reportes_app/fotos")
_MAX_BYTES = 10 * 1024 * 1024
_EXTENSIONES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


async def guardar_foto(file: UploadFile) -> str:
    extension = _EXTENSIONES.get(file.content_type or "")
    if extension is None:
        raise ValidationError("La foto debe ser PNG, JPG o WEBP")
    contenido = await leer_upload(file, _MAX_BYTES)
    FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    (FOTOS_DIR / filename).write_bytes(contenido)
    return filename
