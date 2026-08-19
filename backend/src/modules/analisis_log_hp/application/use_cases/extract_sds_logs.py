"""Caso de uso: extraer logs HP desde el portal SDS por número de serie.

Pipeline (§3.1 caracterización):
1. search_device: serial → device_id + model_name.
2. fetch_event_logs: AJAX XML/CDATA → TSV de 6 columnas + help_urls.
3. Actualiza el catálogo de error codes con URLs de ayuda frescas.
4. Retorna el TSV + metadatos del dispositivo.

Sin fallback a mocks: error claro si el portal falla (§6.1 caracterización).
Timeout total gestionado por el gateway (25 s, §5.12).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.modules.analisis_log_hp.domain.repositories.error_code_repository import (
    ErrorCodeRepository,
)
from src.modules.analisis_log_hp.domain.repositories.hp_insight_gateway import HpInsightGateway
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import HpPortalGateway

logger = logging.getLogger(__name__)

_GENERIC_MODEL = "Generico / Desconocido"


@dataclass
class SdsExtractResult:
    device_id: str
    model_name: str
    tsv: str
    help_urls_updated: int


class ExtractSdsLogs:
    def __init__(
        self,
        portal: HpPortalGateway,
        error_code_repo: ErrorCodeRepository,
        insight: HpInsightGateway,
    ) -> None:
        self._portal = portal
        self._repo = error_code_repo
        self._insight = insight

    async def execute(self, serial: str, days: int = 30) -> SdsExtractResult:
        serial = serial.strip().upper()
        device = await self._portal.search_device(serial)
        device_id = device["id"]
        model_name = await self._resolve_model_name(serial, device.get("model_name", ""))

        result = await self._portal.fetch_event_logs(device_id, days=days)

        updated = 0
        if result.help_urls:
            try:
                updated = await self._repo.bulk_update_solution_urls(result.help_urls)
            except Exception as exc:
                logger.warning(
                    "extract_sds_logs: no se pudo actualizar catálogo con URLs de ayuda",
                    exc_info=exc,
                )

        return SdsExtractResult(
            device_id=device_id,
            model_name=model_name,
            tsv=result.tsv,
            help_urls_updated=updated,
        )

    async def _resolve_model_name(self, serial: str, sds_model_name: str) -> str:
        """Fallback a HP Insight si el scraping SDS no pudo resolver el modelo."""
        if sds_model_name and sds_model_name != _GENERIC_MODEL:
            return sds_model_name
        try:
            device = await self._insight.search_by_serial(serial)
        except Exception as exc:
            logger.warning(
                "extract_sds_logs: fallback a Insight para model_name falló",
                exc_info=exc,
            )
            return sds_model_name or _GENERIC_MODEL
        extended = (device or {}).get("extendedFields") or {}
        return str(extended.get("model") or sds_model_name or _GENERIC_MODEL)
