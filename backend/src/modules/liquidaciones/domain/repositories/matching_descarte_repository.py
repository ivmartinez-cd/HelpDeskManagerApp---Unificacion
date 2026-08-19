"""Puerto de descartes de candidatos de matching N2 (Tabla KM ↔ Siges) —
decisión 0.4.d del plan de matching de sucursales: un rechazo se recuerda,
el mismo candidato no vuelve a proponerse en corridas futuras."""

from typing import Protocol
from uuid import UUID


class MatchingDescarteRepository(Protocol):
    async def create(
        self, tabla_km_id: UUID, siges_sucursal_id: int, usuario_email: str
    ) -> None:
        """Idempotente: si el par ya estaba descartado, no duplica."""
        ...

    async def list_descartados_por_fila(
        self, tabla_km_ids: list[UUID]
    ) -> dict[UUID, set[int]]:
        """`siges_sucursal_id` descartados de cada fila pedida — para
        filtrarlos antes de proponer candidatos N2."""
        ...
