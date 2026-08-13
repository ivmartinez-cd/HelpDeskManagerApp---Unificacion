"""Casos de uso de escritura del catálogo de Prestadores — port de
POST/PATCH/DELETE /prestadores.

`nombre_corto` se normaliza acá (strip+upper), igual que los otros caminos de
escritura (import CSV, Excel maestro) — `get_by_nombre_corto` compara con `==`
case-sensitive, sin esto conviven duplicados que después no matchean."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)


@dataclass(frozen=True)
class ConfigPrestadoresPorts:
    prestadores: PrestadorRepository


class CreatePrestador:
    def __init__(self, ports: ConfigPrestadoresPorts) -> None:
        self._ports = ports

    async def execute(
        self, *, nombre: str, nombre_corto: str, cuit: str | None, region: str | None
    ) -> Prestador:
        return await self._ports.prestadores.create(
            nombre=nombre,
            nombre_corto=nombre_corto.strip().upper(),
            cuit=cuit,
            region=region,
        )


class UpdatePrestador:
    def __init__(self, ports: ConfigPrestadoresPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        prestador_id: UUID,
        *,
        nombre: str,
        nombre_corto: str,
        cuit: str | None,
        region: str | None,
    ) -> Prestador:
        updated = await self._ports.prestadores.update(
            prestador_id,
            nombre=nombre,
            nombre_corto=nombre_corto.strip().upper(),
            cuit=cuit,
            region=region,
        )
        if updated is None:
            raise PrestadorNoEncontradoError(prestador_id)
        return updated


class TogglePrestadorActivo:
    def __init__(self, ports: ConfigPrestadoresPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID, *, activo: bool) -> Prestador:
        updated = await self._ports.prestadores.toggle_activo(prestador_id, activo=activo)
        if updated is None:
            raise PrestadorNoEncontradoError(prestador_id)
        return updated


class DeletePrestador:
    def __init__(self, ports: ConfigPrestadoresPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> None:
        if not await self._ports.prestadores.delete(prestador_id):
            raise PrestadorNoEncontradoError(prestador_id)
