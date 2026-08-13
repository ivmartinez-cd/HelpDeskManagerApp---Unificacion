"""Puerto de tarifarios vigentes por prestador (tarifarios)."""

from datetime import date
from typing import Protocol
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tarifario import Tarifario


class TarifarioRepository(Protocol):
    async def get_by_id(self, tarifario_id: UUID) -> Tarifario | None: ...

    async def list_by_prestador(self, prestador_id: UUID) -> list[Tarifario]:
        """Todos los tarifarios del prestador (vigentes o no) — el motor de reglas
        filtra por vigencia/zona en memoria, no en la query (ver `_resolucion.py`)."""
        ...

    async def list_grupo(
        self, *, prestador_id: UUID, tipo_servicio: str, zona: str | None
    ) -> list[Tarifario]:
        """El grupo (prestador, tipo_servicio, zona) completo — insumo de
        `recalcular_cadena` (ver `domain/services/cadena_tarifaria.py`)."""
        ...

    async def set_vigencia_hasta(self, tarifario_id: UUID, vigencia_hasta: date | None) -> None:
        """Aplica un ajuste de `recalcular_cadena`. Id inexistente = no-op."""
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

    async def update(
        self,
        tarifario_id: UUID,
        *,
        prestador_id: UUID,
        tipo_servicio: str,
        zona: str | None,
        costo_servicio: float,
        costo_km: float,
        vigencia_desde: date,
        vigencia_hasta: date | None,
    ) -> Tarifario | None: ...

    async def delete(self, tarifario_id: UUID) -> bool: ...
