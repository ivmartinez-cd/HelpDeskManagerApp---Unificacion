"""El diagnóstico con IA no deja elegir modelo y acota el contenido."""

import pytest
from pydantic import ValidationError

from src.modules.analisis_log_hp.presentation.schemas.analysis_schemas import AiDiagnoseRequest


def test_ignora_el_modelo_que_mande_el_cliente() -> None:
    req = AiDiagnoseRequest.model_validate({"payload": {"a": 1}, "model": "el-mas-caro"})
    assert not hasattr(req, "model")


def test_rechaza_contenido_gigante() -> None:
    with pytest.raises(ValidationError):
        AiDiagnoseRequest(payload={"log": "x" * 600_000})
