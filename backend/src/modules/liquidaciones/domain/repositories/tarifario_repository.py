"""Puerto de tarifarios vigentes por prestador (tarifarios)."""

from datetime import date
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tarifario import Tarifario


class TarifarioRepository(Protocol):
    async def list_by_prestador(self, prestador_id: UUID) -> list[Tarifario]:
        """Todos los tarifarios del prestador (vigentes o no) — el motor de reglas
        filtra por vigencia/zona en memoria, no en la query (ver `_resolucion.py`)."""
        ...

    async def create(
        self,
        *,
        prestador_id: UUID,
        tipo_servicio: str,
        zona: str | None,
        costo_servicio: float,
        costo_km: float,
        vigencia_desde: date,
        vigencia_hasta: date | None,
    ) -> Tarifario:
        """Genera el `id` (UUID) internamente."""
        ...
