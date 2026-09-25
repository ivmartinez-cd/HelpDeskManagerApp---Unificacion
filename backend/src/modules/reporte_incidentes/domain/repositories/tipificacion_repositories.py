from typing import Protocol

from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)


class TaxonomiaRepository(Protocol):
    async def listar(self) -> list[Categoria]:
        """Categorías en el orden configurado."""
        ...

    async def crear(self, categoria: Categoria) -> None:
        """Alta al final del orden."""
        ...

    async def reemplazar(self, nombre_anterior: str, categoria: Categoria) -> None:
        """Reemplaza la categoría (y sus subcategorías) conservando su lugar."""
        ...

    async def eliminar(self, nombre: str) -> None:
        ...


class TipificacionCacheRepository(Protocol):
    async def obtener(self, claves: set[str]) -> dict[str, TipificacionGuardada]:
        """Tipificaciones guardadas para esas claves de caso (las que falten no vienen)."""
        ...

    async def guardar(self, tipificaciones: dict[str, TipificacionGuardada]) -> None:
        """Alta o reemplazo por clave de caso."""
        ...
