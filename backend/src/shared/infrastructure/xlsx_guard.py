"""Un .xlsx es un zip: unos KB pueden descomprimirse en GB y tumbar al backend al
abrirlo con openpyxl/pandas (auditoría de seguridad 2026-09-30). Se mira el
tamaño declarado de cada entrada antes de parsear."""

import zipfile
from io import BytesIO
from pathlib import Path

from src.shared.domain.errors import ValidationError

MAX_XLSX_DESCOMPRIMIDO = 300 * 1024 * 1024


def verificar_xlsx_acotado(origen: bytes | str | Path) -> None:
    fuente = BytesIO(origen) if isinstance(origen, bytes) else origen
    try:
        with zipfile.ZipFile(fuente) as zf:
            total = sum(info.file_size for info in zf.infolist())
    except zipfile.BadZipFile:
        return  # no es un xlsx (ej. .xls viejo): que lo rechace el parser con su error
    if total > MAX_XLSX_DESCOMPRIMIDO:
        raise ValidationError("El Excel es demasiado grande una vez descomprimido")
