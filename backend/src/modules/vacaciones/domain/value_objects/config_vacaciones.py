from dataclasses import dataclass

from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier


@dataclass(frozen=True, slots=True)
class ConfigVacaciones:
    """Config del módulo (singleton `vacaciones_config`).

    `min_advance_notice_days` / `max_overlap_percent` / `max_overlap_count`
    existen por paridad de datos y se editan desde la pantalla Configuración,
    pero NINGUNA validación los usa (el legacy tampoco) — no agregar lógica
    sobre ellos sin decisión explícita.
    """

    seniority_tiers: tuple[SeniorityTier, ...]
    next_year_open_month: int
    next_year_open_day: int
    allow_advance_request: bool
    max_advance_days: int
    allow_carry_over: bool
    max_carry_over_days: int
    min_advance_notice_days: int = 7
    max_overlap_percent: int = 50
    max_overlap_count: int = 0
