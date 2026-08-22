"""AnthropicAiGateway con el cliente Anthropic reemplazado por un stub: extracción
robusta del JSON de la respuesta, conteo de tokens y parámetros del request."""

import json
from types import SimpleNamespace
from typing import Any

import pytest

from src.modules.analisis_log_hp.infrastructure.anthropic.anthropic_ai_gateway import (
    AnthropicAiGateway,
    _extract_json,
    _parse_tokens,
)


class TestExtractJson:
    @pytest.mark.parametrize(
        "texto",
        [
            '{"despacho": "si"}',
            '```json\n{"despacho": "si"}\n```',
            'Acá va el diagnóstico:\n{"despacho": "si"}\nfin',
        ],
    )
    def test_extrae_json_limpio_con_fence_o_con_texto_alrededor(self, texto: str) -> None:
        assert _extract_json(texto) == {"despacho": "si"}

    def test_sin_json_devuelve_none(self) -> None:
        assert _extract_json("no hay nada { roto") is None


class TestParseTokens:
    def test_mapea_los_cuatro_contadores_con_cero_por_defecto(self) -> None:
        usage = SimpleNamespace(
            input_tokens=10, output_tokens=5, cache_creation_input_tokens=None
        )
        assert _parse_tokens(usage) == {
            "input": 10, "output": 5, "cache_write": 0, "cache_read": 0
        }


class _Messages:
    def __init__(self, text: str, stop_reason: str = "end_turn") -> None:
        self._text = text
        self._stop = stop_reason
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(text=self._text)],
            stop_reason=self._stop,
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )


def _gateway(text: str, stop_reason: str = "end_turn") -> tuple[AnthropicAiGateway, _Messages]:
    gw = AnthropicAiGateway(api_key="sk-test")
    messages = _Messages(text, stop_reason)
    gw._client = SimpleNamespace(messages=messages)  # type: ignore[assignment]
    return gw, messages


class TestDiagnose:
    async def test_devuelve_json_normalizado_y_tokens(self) -> None:
        gw, messages = _gateway('```json\n{"despacho": "remoto", "prioridad": "alta"}\n```')
        text, tokens = await gw.diagnose({"incidents": [{"code": "13.20"}]}, "claude-x")
        assert json.loads(text) == {"despacho": "remoto", "prioridad": "alta"}
        assert tokens == {"input": 100, "output": 20, "cache_write": 0, "cache_read": 0}
        assert messages.kwargs["model"] == "claude-x"
        assert messages.kwargs["max_tokens"] == 2048
        assert "13.20" in messages.kwargs["messages"][0]["content"]
        assert messages.kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}

    async def test_respuesta_sin_json_devuelve_el_texto_crudo(self) -> None:
        gw, _ = _gateway("no pude diagnosticar", stop_reason="max_tokens")
        text, _ = await gw.diagnose({}, "m")
        assert text == "no pude diagnosticar"


class TestGeneratePdfSummary:
    async def test_devuelve_el_texto_strip_y_usa_max_tokens_chico(self) -> None:
        gw, messages = _gateway("  resumen ejecutivo  ")
        text, tokens = await gw.generate_pdf_summary({"diagnostico": "x"}, "m")
        assert text == "resumen ejecutivo"
        assert tokens["input"] == 100
        assert messages.kwargs["max_tokens"] == 512
