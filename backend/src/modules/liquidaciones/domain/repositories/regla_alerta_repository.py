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

    async def set_genera_observaciones(self, codigo: str, valor: bool) -> ReglaAlerta | None:
        """Segundo switch de ALT005 — ver `regla_alerta.genera_observaciones`.
        Merge sobre `configuracion` (no reemplaza la clave completa), para no
        pisar otros parámetros que se agreguen a futuro. None si el código no
        existe."""
        ...
