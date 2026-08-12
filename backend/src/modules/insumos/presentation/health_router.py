"""Health check específico de Insight — detecta credenciales inválidas o el servicio
caído antes de que el usuario vea la UI congelada. Puerto de `GET /api/health` del
legacy, con Canal Directo omitido: `SoapOrderClient.ensure_login()` era un no-op ahí
(vestigio de una implementación anterior que sí precalentaba el login del portal), así
que no hay ningún chequeo real de Canal Directo para portar.
"""

import logging

from fastapi import APIRouter, Depends, Response, status

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.insumos.presentation.wiring import get_insight_gateway
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))


@router.get("/health")
async def get_insumos_health(
    response: Response,
    _: Identity = _require_view,
    gateway: InsightGateway = Depends(get_insight_gateway),
) -> dict[str, object]:
    try:
        await gateway.ping()
    except ExternalServiceError as exc:
        logger.warning(
            "insumos health check: Insight API no disponible", extra={"error": str(exc)}
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ok": False, "errors": ["Insight API: no disponible"]}
    return {"ok": True}
