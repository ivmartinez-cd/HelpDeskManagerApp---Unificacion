import pytest

from src.modules.reporte_incidentes.domain.errors import IaNoConfiguradaError
from src.modules.reporte_incidentes.infrastructure.gemini.gemini_clasificador import (
    GeminiClasificador,
    _a_respuesta,
)


def _clasificador(api_key: str = "k") -> GeminiClasificador:
    return GeminiClasificador(api_key, ("m1", "m1", "m2", ""), (1, 5.0))


def test_el_pedido_pide_json_con_schema_y_thinking_budget_sin_temperature() -> None:
    cuerpo = _clasificador()._cuerpo("hola")
    config = cuerpo["generationConfig"]
    assert cuerpo["contents"][0]["parts"][0]["text"] == "hola"
    assert config["responseMimeType"] == "application/json"
    assert config["thinkingConfig"] == {"thinkingBudget": 1}
    assert config["responseSchema"]["items"]["required"] == [
        "i", "categoria", "subcategoria", "confianza",
    ]
    assert "temperature" not in config


def test_modelos_sin_repetidos_ni_vacios() -> None:
    assert _clasificador()._modelos == ("m1", "m2")


def test_lee_texto_y_tokens_ignorando_partes_de_pensamiento() -> None:
    datos = {
        "candidates": [{"content": {"parts": [
            {"text": "razono...", "thought": True}, {"text": "[{\"i\": 0}"}, {"text": "]"},
        ]}}],
        "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 8},
    }
    r = _a_respuesta(datos, "m1")
    assert (r.texto, r.tokens_entrada, r.tokens_salida, r.modelo) == ('[{"i": 0}]', 120, 8, "m1")


async def test_sin_clave_no_llama_y_avisa() -> None:
    clasificador = _clasificador(api_key="")
    assert not clasificador.configurado
    with pytest.raises(IaNoConfiguradaError):
        await clasificador.clasificar("x")
