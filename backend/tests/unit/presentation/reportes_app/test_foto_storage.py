"""Fotos de los reportes: solo imágenes, nombre generado (nunca el del usuario)."""

import io
from pathlib import Path

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from src.modules.reportes_app.presentation import foto_storage
from src.shared.domain.errors import ValidationError


def _upload(content_type: str, nombre: str = "../../captura.png") -> UploadFile:
    return UploadFile(
        io.BytesIO(b"datos"), filename=nombre, headers=Headers({"content-type": content_type})
    )


async def test_guarda_la_imagen_con_nombre_generado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(foto_storage, "FOTOS_DIR", tmp_path)
    filename = await foto_storage.guardar_foto(_upload("image/png"))
    assert filename.endswith(".png") and "captura" not in filename
    assert (tmp_path / filename).read_bytes() == b"datos"


async def test_rechaza_lo_que_no_es_imagen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(foto_storage, "FOTOS_DIR", tmp_path)
    with pytest.raises(ValidationError):
        await foto_storage.guardar_foto(_upload("application/pdf"))
    assert not any(tmp_path.iterdir())
