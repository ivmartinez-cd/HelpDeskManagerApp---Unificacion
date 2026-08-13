import uuid
from datetime import date
from typing import Protocol

from src.modules.vacaciones.domain.entities.feriado import Feriado


class FeriadoRepository(Protocol):
    async def list_all(self) -> list[Feriado]: ...

    async def get_by_id(self, feriado_id: uuid.UUID) -> Feriado | None: ...

    async def get_by_date(self, fecha: date) -> Feriado | None: ...

    async def existe_no_deduce_en(self, fecha: date) -> bool:
        """¿Hay feriado con deducts_vacation=False exactamente en `fecha`?
        (el único caso que descuenta un día del conteo legacy)."""
        ...

    async def upsert_por_fecha(self, feriado: Feriado) -> None:
        """Insert o update por la fecha (unique); pisa nombre y
        deducts_vacation — semántica del import legacy."""
        ...

    async def add(self, feriado: Feriado) -> None: ...

    async def save(self, feriado: Feriado) -> None: ...

    async def delete(self, feriado_id: uuid.UUID) -> None: ...
