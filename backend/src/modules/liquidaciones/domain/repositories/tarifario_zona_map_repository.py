"""Puerto del mapeo descripción-Siges → SPST (tarifario_zona_maps, ADR-014)."""

from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tarifario_zona_map import TarifarioZonaMap


class TarifarioZonaMapRepository(Protocol):
    async def list_all(self) -> list[TarifarioZonaMap]: ...

    async def upsert(
        self, *, prestador_id: UUID, descripcion_siges: str, spst_id: UUID | None
    ) -> TarifarioZonaMap:
        """Crea o pisa el mapeo del par (prestador, descripción) — re-mapear es
        la forma de corregir un mapeo equivocado. `spst_id=None` = tarifa
        genérica (sin SPST específico)."""
        ...
