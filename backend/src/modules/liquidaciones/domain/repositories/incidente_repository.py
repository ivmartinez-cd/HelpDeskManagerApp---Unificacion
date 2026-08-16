"""Puerto de incidentes cobrados dentro de una liquidación (incidentes)."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)
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

    async def bulk_create(
        self, liquidacion_id: UUID, incidentes: Sequence[IncidenteImportado]
    ) -> list[Incidente]:
        """Crea los incidentes recién parseados de una liquidación — `estado_validacion`
        arranca en "pendiente" y los `*_esperado` en `None`, los fija recién el motor
        de reglas al reanalizar (`apply_evaluacion`), igual que al importar."""
        ...

    async def apply_evaluacion(self, resultados: Sequence[IncidenteEvaluado]) -> None:
        """Persiste el enriquecimiento (`*_esperado`, `estado_validacion`) que
        devuelve `ejecutar_motor_reglas` — en el legacy era una mutación directa del
        ORM, acá es un update explícito porque `Incidente` es inmutable."""
        ...

    async def empresas_con_actividad_reciente(
        self, prestador_id: UUID, desde_periodo: str
    ) -> set[str]:
        """Distinct empresa_nombre (sin normalizar) de incidentes de este prestador
        en liquidaciones con periodo >= desde_periodo. Sirve para detectar ex-clientes."""
        ...
