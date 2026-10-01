"""Lectura acotada de uploads y guardia de Excel comprimidos."""

import io
import zipfile

import pytest
from fastapi import UploadFile

from src.shared.domain.errors import ValidationError
from src.shared.infrastructure import xlsx_guard
from src.shared.presentation.uploads import ArchivoDemasiadoGrandeError, leer_upload


async def test_lee_completo_si_no_pasa_el_tope() -> None:
    contenido = b"x" * 3000
    assert await leer_upload(UploadFile(io.BytesIO(contenido)), max_bytes=3000) == contenido


async def test_corta_apenas_pasa_el_tope() -> None:
    with pytest.raises(ArchivoDemasiadoGrandeError) as exc:
        await leer_upload(UploadFile(io.BytesIO(b"x" * 3001)), max_bytes=3000)
    assert exc.value.http_status == 413


def _zip(tamano: int) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("xl/hoja.xml", b"0" * tamano)
    return buf.getvalue()


def test_xlsx_que_descomprime_de_mas_se_rechaza(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(xlsx_guard, "MAX_XLSX_DESCOMPRIMIDO", 1000)
    bomba = _zip(5000)
    assert len(bomba) < 1000  # chico comprimido, grande descomprimido
    with pytest.raises(ValidationError):
        xlsx_guard.verificar_xlsx_acotado(bomba)
    xlsx_guard.verificar_xlsx_acotado(_zip(500))
    xlsx_guard.verificar_xlsx_acotado(b"no es un zip")
