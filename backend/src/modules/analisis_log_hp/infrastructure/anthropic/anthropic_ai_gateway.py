"""Adapter del cliente Anthropic para diagnóstico y resumen PDF.

Port del servicio de IA del legacy (ai_diagnosis_service.py + ai_pdf_service.py).
El prompt de diagnóstico es lógica de negocio real — se porta textual (§5.8).
Sin créditos Anthropic hoy: implementado pero no probado en vivo (§6.5).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

# Prompt de diagnóstico portado textual del legacy (ver ai_diagnosis_service.py).
# NO reescribir: contiene reglas de despacho de visita técnica que son negocio real.
_DIAGNOSE_SYSTEM_PROMPT = (
    "Sos el Arquitecto de Soporte Técnico Enterprise para impresoras HP LaserJet de alta gama.\n"
    "Tu laburo es dar un diagnóstico de nivel INGENIERÍA cruzando todas las fuentes de datos disponibles.\n\n"
    "DATOS QUE TENÉS:\n"
    "- incidents[]: código, severidad, ocurrencias, start/end (fecha primera y última ocurrencia), counter_range [min, max] del error, y technical_solution oficial de HP.\n"
    "- metadata.counter_range: [counter_mínimo, counter_máximo] del log completo — el máximo es el último evento registrado.\n"
    "- metadata.date_range: rango de fechas del log (formato: 'YYYY-MM-DD HH:MM – YYYY-MM-DD HH:MM').\n"
    "- metadata.alerts_history[]: alertas Insight con fecha y engineCycles.\n"
    "- metadata.consumables[]: nivel de tóner/tambor en porcentaje.\n"
    "- metadata.meters_pattern[]: historial de contadores del equipo.\n"
    "- metadata.cds_incidents[]: historial de incidentes de Canal Directo (últimos 12 meses).\n\n"
    "PASO 0 — VOLUMEN DIARIO:\n"
    "  vol_diario = (counter_máximo - counter_mínimo del log) / días_del_log\n"
    "  umbral = max(vol_diario × 7, 400)\n\n"
    "PASO 1 — RECENCY (doble check: delta + recency temporal):\n"
    "  delta = counter_máximo_del_log - counter_máximo_del_error\n"
    "  días_desde_último = (fecha_fin_del_log - end_del_incidente) en días\n"
    "ACTIVO si: delta < umbral O días_desde_último ≤ 7\n"
    "  ACTIVO-CRÍTICO: delta < umbral/7 O días_desde_último ≤ 2\n"
    "  ACTIVO-MODERADO: no crítico pero ACTIVO\n"
    "RESUELTO: delta ≥ umbral Y días_desde_último > 7\n\n"
    "PASO 2 — DIAGNÓSTICO: módulo afectado, correlación con Insight/consumibles, activos vs. resueltos.\n\n"
    "PASO 3 — URGENCIA: urgente (ACTIVO-CRÍTICO) | programar (ACTIVO-MODERADO) | monitorear (RESUELTO)\n\n"
    "PASO 4 — DESPACHO:\n"
    "HW FÍSICO (requieren manos): familia 13/50/51/52/54/57/59/55.xx\n"
    "REMOTO/USUARIO: familia 41/10/98/99/33.xx\n"
    "REINCIDENCIA (gate OBLIGATORIO): HW físico DESPACHABLE solo si ACTIVO Y (occurrences > 1 O ráfaga).\n"
    "Un HW activo con occurrences == 1 sin ráfaga → NUNCA 'si'; como mucho 'remoto'.\n"
    "1. 'si': ≥1 HW físico DESPACHABLE (ACTIVO + reincidente/ráfaga)\n"
    "2. 'remoto': sin HW despachable, pero errores config/fw/consumibles ACTIVOS o HW único aislado\n"
    "3. 'no': TODOS los HW físicos RESUELTOS\n\n"
    "Respondé ÚNICAMENTE con este JSON:\n"
    '{\n'
    '  "_volumen": "[vol_diario y umbral calculados]",\n'
    '  "_hw_deltas": "[delta, días, occ y clasificación por código HW]",\n'
    '  "_despacho_logica": "[conclusión de despacho]",\n'
    '  "despacho": "si/no/remoto",\n'
    '  "despacho_motivo": "[una frase corta, max 20 palabras]",\n'
    '  "urgencia": "urgente/programar/monitorear",\n'
    '  "prioridad": "alta/media/baja",\n'
    '  "tareas_resumen": "[max 46 palabras, instrucción directa al técnico]",\n'
    '  "diagnostico": "[max 120 palabras, párrafos, sin counters/deltas]",\n'
    '  "acciones": ["[acción 1]", "[acción 2]"],\n'
    '  "impacto": "[consecuencia si no se interviene]"\n'
    "}\n"
    "Sin texto fuera del JSON. Sin markdown externo."
)

_PDF_SYSTEM_PROMPT = (
    "Generá un resumen ejecutivo conciso (máx 150 palabras) del diagnóstico técnico de la impresora HP "
    "para incluir en un reporte PDF. Estilo profesional, en español rioplatense. "
    "Sin mencionar counters, deltas ni valores numéricos de páginas. "
    "Respondé solo con el texto del resumen, sin JSON ni markdown."
)


def _extract_json(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if m:
        try:
            return json.loads(m.group())  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass
    logger.warning("No se pudo extraer JSON de la respuesta IA: %s", text[:200])
    return None


def _parse_tokens(usage: Any) -> dict[str, int]:
    return {
        "input": getattr(usage, "input_tokens", 0) or 0,
        "output": getattr(usage, "output_tokens", 0) or 0,
        "cache_write": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
    }


class AnthropicAiGateway:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)

    async def diagnose(
        self, payload: dict[str, Any], model: str
    ) -> tuple[str, dict[str, int]]:
        response = await self._client.messages.create(
            model=model,
            max_tokens=2048,
            system=[{"type": "text", "text": _DIAGNOSE_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)}],
        )
        raw = response.content[0].text
        if getattr(response, "stop_reason", None) == "max_tokens":
            logger.warning("diagnose: respuesta truncada por max_tokens: %s", raw[:200])
        parsed = _extract_json(raw)
        text = json.dumps(parsed, ensure_ascii=False) if parsed else raw
        return text, _parse_tokens(response.usage)

    async def generate_pdf_summary(
        self, payload: dict[str, Any], model: str
    ) -> tuple[str, dict[str, int]]:
        response = await self._client.messages.create(
            model=model,
            max_tokens=512,
            system=[{"type": "text", "text": _PDF_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)}],
        )
        raw = response.content[0].text
        return raw.strip(), _parse_tokens(response.usage)
