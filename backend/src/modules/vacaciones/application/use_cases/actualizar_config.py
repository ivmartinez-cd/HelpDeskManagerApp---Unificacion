"""PUT /config (paridad settings.controller legacy): merge parcial sobre el
singleton — solo pisa los campos presentes en el comando — y auditoría con la
lista de claves cambiadas."""

from dataclasses import dataclass, fields, replace

from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_UPDATE,
    ENTIDAD_CONFIG,
)
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.config_repository import ConfigRepository
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones
from src.modules.vacaciones.domain.value_objects.seniority_tier import SeniorityTier


@dataclass(frozen=True, slots=True)
class ActualizarConfigCommand:
    """None = no tocar ese campo (el PUT legacy era parcial)."""

    seniority_tiers: tuple[SeniorityTier, ...] | None = None
    min_advance_notice_days: int | None = None
    max_overlap_percent: int | None = None
    max_overlap_count: int | None = None
    next_year_open_month: int | None = None
    next_year_open_day: int | None = None
    allow_advance_request: bool | None = None
    max_advance_days: int | None = None
    allow_carry_over: bool | None = None
    max_carry_over_days: int | None = None


@dataclass(frozen=True, slots=True)
class ActualizarConfigDependencies:
    config: ConfigRepository
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()


class ActualizarConfig:
    def __init__(self, deps: ActualizarConfigDependencies) -> None:
        self._deps = deps

    async def execute(self, command: ActualizarConfigCommand) -> ConfigVacaciones:
        actual = await self._deps.config.get()
        cambios = {
            f.name: getattr(command, f.name)
            for f in fields(command)
            if getattr(command, f.name) is not None
        }
        nueva = replace(actual, **cambios)
        await self._deps.config.save(nueva)
        await self._deps.auditoria.registrar(
            ACCION_UPDATE,
            ENTIDAD_CONFIG,
            "singleton",
            {"changes": sorted(cambios.keys())},
        )
        return nueva
