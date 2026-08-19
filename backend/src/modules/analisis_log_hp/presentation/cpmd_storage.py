"""Storage en disco de los PDFs de manuales CPMD.

Mismo patrón que `contadores/presentation/upload_storage.py`: directorio bajo
`var/` dentro del bind-mount del backend (persiste en el host, no es un
volumen anónimo). A diferencia de contadores, acá el archivo es permanente
(no se borra tras procesar) — se sirve por `manual_id`, nunca por nombre de
archivo crudo, así que no hay riesgo de path traversal en el endpoint de
lectura.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from src.shared.infrastructure.config.settings import get_settings


def cpmd_dir() -> Path:
    path = Path(get_settings().analisis_log_hp_cpmd_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_cpmd_pdf(file: UploadFile) -> str:
    """Guarda el PDF con un nombre único y devuelve el nombre de archivo (no el path)."""
    filename = f"{uuid.uuid4().hex}.pdf"
    (cpmd_dir() / filename).write_bytes(await file.read())
    return filename
