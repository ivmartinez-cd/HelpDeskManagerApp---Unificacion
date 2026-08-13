from dataclasses import dataclass

from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier


@dataclass(frozen=True, slots=True)
class ConfigVacaciones:
    """Config del módulo (singleton `vacaciones_config`). Los campos del legacy
    que ninguna validación usa (`min_advance_notice_days`, `max_overlap_*`) no
    se exponen acá a propósito: viven solo en la tabla por paridad de datos.
    """

    seniority_tiers: tuple[SeniorityTier, ...]
    next_year_open_month: int
    next_year_open_day: int
    allow_advance_request: bool
    max_advance_days: int
    allow_carry_over: bool
    max_carry_over_days: int
