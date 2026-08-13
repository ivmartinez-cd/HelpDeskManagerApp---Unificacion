import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones
from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier
from src.modules.vacaciones.infrastructure.models.config_model import VacacionesConfigModel

_logger = logging.getLogger(__name__)

_SINGLETON_ID = "singleton"


def _parse_tiers(raw: object) -> tuple[SeniorityTier, ...]:
    """Tiers desde JSONB (claves snake_case). Entradas inválidas se descartan
    con warning; si no queda ninguna, el dominio usa sus defaults (paridad con
    getSeniorityTiers del legacy, que devolvía undefined ante datos raros)."""
    if not isinstance(raw, list):
        return ()
    tiers: list[SeniorityTier] = []
    for item in raw:
        try:
            tiers.append(
                SeniorityTier(
                    min_years=float(item["min_years"]),
                    max_years=float(item["max_years"]),
                    days=int(item["days"]),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            _logger.warning(
                "Tier de antigüedad inválido en vacaciones_config, se ignora",
                extra={"item": item},
                exc_info=exc,
            )
    return tuple(tiers)


class SqlAlchemyConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> ConfigVacaciones:
        row = await self._session.get(VacacionesConfigModel, _SINGLETON_ID)
        if row is None:
            # La migración siembra el singleton; si falta es un despliegue roto.
            raise RuntimeError("vacaciones_config singleton no encontrado")
        return ConfigVacaciones(
            seniority_tiers=_parse_tiers(row.seniority_tiers),
            next_year_open_month=row.next_year_open_month,
            next_year_open_day=row.next_year_open_day,
            allow_advance_request=row.allow_advance_request,
            max_advance_days=row.max_advance_days,
            allow_carry_over=row.allow_carry_over,
            max_carry_over_days=row.max_carry_over_days,
            min_advance_notice_days=row.min_advance_notice_days,
            max_overlap_percent=row.max_overlap_percent,
            max_overlap_count=row.max_overlap_count,
        )

    async def save(self, config: ConfigVacaciones) -> None:
        row = await self._session.get(VacacionesConfigModel, _SINGLETON_ID)
        if row is None:
            raise RuntimeError("vacaciones_config singleton no encontrado")
        row.seniority_tiers = [
            {"min_years": t.min_years, "max_years": t.max_years, "days": t.days}
            for t in config.seniority_tiers
        ]
        row.next_year_open_month = config.next_year_open_month
        row.next_year_open_day = config.next_year_open_day
        row.allow_advance_request = config.allow_advance_request
        row.max_advance_days = config.max_advance_days
        row.allow_carry_over = config.allow_carry_over
        row.max_carry_over_days = config.max_carry_over_days
        row.min_advance_notice_days = config.min_advance_notice_days
        row.max_overlap_percent = config.max_overlap_percent
        row.max_overlap_count = config.max_overlap_count
        await self._session.flush()
