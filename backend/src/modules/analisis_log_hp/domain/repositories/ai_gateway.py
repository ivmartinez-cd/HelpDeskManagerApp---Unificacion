"""Puerto: gateway de IA (Anthropic Claude)."""

from typing import Any, Protocol


class AiGateway(Protocol):
    async def diagnose(self, payload: dict[str, Any], model: str) -> tuple[str, dict[str, int]]:
        """Diagnóstico IA. Retorna (json_diagnosis_str, tokens_dict)."""
        ...

    async def generate_pdf_summary(
        self, payload: dict[str, Any], model: str
    ) -> tuple[str, dict[str, int]]:
        """Resumen ejecutivo para PDF. Retorna (summary_str, tokens_dict)."""
        ...
