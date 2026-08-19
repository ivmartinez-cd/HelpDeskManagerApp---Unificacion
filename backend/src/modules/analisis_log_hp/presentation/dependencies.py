"""Inyección de dependencias del módulo analisis-log-hp.

Singleton de gateways: una instancia por proceso (sesión HTTP persistida).
Repos SQLAlchemy: una instancia por request (sesión de DB).
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.infrastructure.anthropic.anthropic_ai_gateway import (
    AnthropicAiGateway,
)
from src.modules.analisis_log_hp.infrastructure.hp_insight.httpx_hp_insight_gateway import (
    HttpxHpInsightGateway,
)
from src.modules.analisis_log_hp.infrastructure.hp_portal.httpx_hp_portal_gateway import (
    HttpxHpPortalGateway,
)
from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_cpmd_manual_repository import (  # noqa: E501
    SqlAlchemyCpmdManualRepository,
)
from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_error_code_repository import (  # noqa: E501
    SqlAlchemyErrorCodeRepository,
)
from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_saved_analysis_repository import (  # noqa: E501
    SqlAlchemySavedAnalysisRepository,
)
from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_telemetry_repository import (  # noqa: E501
    SqlAlchemyTelemetryRepository,
)
from src.modules.analisis_log_hp.infrastructure.wsayc.zeep_cds_gateway import ZeepCdsGateway
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def get_hp_portal_gateway() -> HttpxHpPortalGateway:
    s = get_settings()
    return HttpxHpPortalGateway(
        username=s.sds_portal_username,
        password=s.sds_portal_password.get_secret_value(),
    )


@lru_cache
def get_hp_insight_gateway() -> HttpxHpInsightGateway:
    s = get_settings()
    return HttpxHpInsightGateway(
        base_url=s.insight_base_url,
        api_key=s.insight_api_key,
        api_secret=s.insight_api_secret.get_secret_value(),
    )


@lru_cache
def get_ai_gateway() -> AnthropicAiGateway:
    s = get_settings()
    return AnthropicAiGateway(api_key=s.anthropic_api_key)


def get_error_code_repo(db: AsyncSession) -> SqlAlchemyErrorCodeRepository:
    return SqlAlchemyErrorCodeRepository(db)


def get_saved_analysis_repo(db: AsyncSession) -> SqlAlchemySavedAnalysisRepository:
    return SqlAlchemySavedAnalysisRepository(db)


def get_telemetry_repo(db: AsyncSession) -> SqlAlchemyTelemetryRepository:
    return SqlAlchemyTelemetryRepository(db)


def get_cpmd_manual_repo(db: AsyncSession) -> SqlAlchemyCpmdManualRepository:
    return SqlAlchemyCpmdManualRepository(db)


@lru_cache
def get_cds_wsayc_gateway() -> ZeepCdsGateway:
    return ZeepCdsGateway()
