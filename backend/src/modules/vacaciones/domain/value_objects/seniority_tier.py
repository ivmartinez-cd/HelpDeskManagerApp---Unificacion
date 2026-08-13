from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeniorityTier:
    """Rango de antigüedad → días de vacaciones. `min_years` inclusive,
    `max_years` exclusivo (semántica del legacy: `years >= min && years < max`).
    """

    min_years: float
    max_years: float
    days: int


# Fallback del legacy (`DEFAULT_TIERS` en cycle.service.ts) para el caso en que
# la config no tenga tiers válidos. La config sembrada usa los 7 tiers del
# default de Prisma; estos 5 solo aplican si alguien la vacía.
DEFAULT_TIERS: tuple[SeniorityTier, ...] = (
    SeniorityTier(min_years=0, max_years=0.5, days=7),
    SeniorityTier(min_years=0.5, max_years=5, days=14),
    SeniorityTier(min_years=5, max_years=10, days=21),
    SeniorityTier(min_years=10, max_years=20, days=28),
    SeniorityTier(min_years=20, max_years=99, days=35),
)
