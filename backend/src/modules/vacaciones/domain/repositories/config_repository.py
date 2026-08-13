from typing import Protocol

from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones


class ConfigRepository(Protocol):
    async def get(self) -> ConfigVacaciones:
        """Config singleton (sembrada por migración: siempre existe)."""
        ...

    async def save(self, config: ConfigVacaciones) -> None:
        """Pisa el singleton completo (el merge parcial del PUT legacy lo
        resuelve el use case leyendo primero)."""
        ...
