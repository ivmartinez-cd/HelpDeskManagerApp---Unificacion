"""Puerto del catálogo de reglas del motor de alertas (reglas_alerta)."""

from typing import Protocol

from src.modules.liquidaciones.domain.entities.regla_alerta import ReglaAlerta


class ReglaAlertaRepository(Protocol):
    async def list_activas(self) -> dict[str, ReglaAlerta]:
        """Reglas con `activa=True`, indexadas por `codigo` — listas para pasarle
        directo a `ejecutar_motor_reglas`."""
        ...

    async def list_all(self) -> list[ReglaAlerta]: ...

    async def set_activa(self, codigo: str, activa: bool) -> ReglaAlerta | None:
        """Prende/apaga una regla. Aplica en el próximo re-análisis (el motor
        consulta `list_activas` en cada corrida); las alertas ya generadas no
        se tocan. None si el código no existe."""
        ...
