"""Caso de uso: diagnóstico IA con modelo seleccionable.

El diagnóstico no se auto-persiste — guardar es decisión del usuario (§3.6).
Sin créditos Anthropic hoy: implementado pero no probado en vivo (§6.5).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.modules.analisis_log_hp.domain.repositories.ai_gateway import AiGateway

logger = logging.getLogger(__name__)

_PRICE_INPUT = 3.00
_PRICE_OUTPUT = 15.00
_PRICE_CACHE_WRITE = 3.75
_PRICE_CACHE_READ = 0.30


def _cost(tokens: dict[str, int]) -> float:
    return (
        tokens.get("input", 0) * _PRICE_INPUT / 1_000_000
        + tokens.get("output", 0) * _PRICE_OUTPUT / 1_000_000
        + tokens.get("cache_write", 0) * _PRICE_CACHE_WRITE / 1_000_000
        + tokens.get("cache_read", 0) * _PRICE_CACHE_READ / 1_000_000
    )


@dataclass
class DiagnoseAiResult:
    diagnosis: str
    tokens: dict[str, int]
    cost_usd: float


class DiagnoseAi:
    def __init__(self, ai: AiGateway) -> None:
        self._ai = ai

    async def execute(self, payload: dict[str, Any], model: str) -> DiagnoseAiResult:
        text, tokens = await self._ai.diagnose(payload, model)
        return DiagnoseAiResult(diagnosis=text, tokens=tokens, cost_usd=_cost(tokens))


class GeneratePdfSummary:
    def __init__(self, ai: AiGateway) -> None:
        self._ai = ai

    async def execute(self, payload: dict[str, Any], model: str) -> DiagnoseAiResult:
        text, tokens = await self._ai.generate_pdf_summary(payload, model)
        return DiagnoseAiResult(diagnosis=text, tokens=tokens, cost_usd=_cost(tokens))


class ListAiModels:
    def __init__(self, ai: AiGateway) -> None:
        self._ai = ai

    async def execute(self) -> list[dict[str, Any]]:
        return await self._ai.list_models()
