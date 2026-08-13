from typing import Protocol

from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones


class ConfigRepository(Protocol):
    async def get(self) -> ConfigVacaciones:
        """Config singleton (sembrada por migración: siempre existe)."""
        ...
