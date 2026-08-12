"""Puerto de incidentes cobrados dentro de una liquidación (incidentes).

Sin `create`/`bulk_create` todavía: la importación de incidentes desde CSV (que es
quien los crearía) es un caso de uso que no se portó en esta ronda — agregar el método
recién cuando haya un caller real que valide la forma del payload, no antes."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    IncidenteEvaluado,
)


class IncidenteRepository(Protocol):
    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Incidente]: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[Incidente]:
        """Todos los incidentes de TODAS las liquidaciones del prestador — ALT003
        (viático duplicado) y ALT004 (servicio duplicado) comparan contra el
        histórico completo, no solo contra la liquidación que se está evaluando."""
        ...

    async def apply_evaluacion(self, resultados: Sequence[IncidenteEvaluado]) -> None:
        """Persiste el enriquecimiento (`*_esperado`, `estado_validacion`) que
        devuelve `ejecutar_motor_reglas` — en el legacy era una mutación directa del
        ORM, acá es un update explícito porque `Incidente` es inmutable."""
        ...
