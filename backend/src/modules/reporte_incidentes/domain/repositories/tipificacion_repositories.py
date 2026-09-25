from typing import Protocol

from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)


class TaxonomiaRepository(Protocol):
    async def listar(self) -> list[Categoria]:
        """Categorías en el orden configurado."""
        ...


class TipificacionCacheRepository(Protocol):
    async def obtener(self, claves: set[str]) -> dict[str, TipificacionGuardada]:
        """Tipificaciones guardadas para esas claves de caso (las que falten no vienen)."""
        ...

    async def guardar(self, tipificaciones: dict[str, TipificacionGuardada]) -> None:
        """Alta o reemplazo por clave de caso."""
        ...
