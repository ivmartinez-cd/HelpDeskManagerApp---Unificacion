"""Casos de uso de escritura del catálogo de Prestadores — port de
POST/PATCH/DELETE /prestadores.

`nombre_corto` se normaliza acá (strip+upper), igual que los otros caminos de
escritura (import CSV, Excel maestro) — `get_by_nombre_corto` compara con `==`
case-sensitive, sin esto conviven duplicados que después no matchean."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.errors import (
    PrestadorDuplicadoError,
    PrestadorNoEncontradoError,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)


@dataclass(frozen=True)
class ConfigPrestadoresPorts:
    prestadores: PrestadorRepository


async def _asegurar_nombre_corto_libre(
    repo: PrestadorRepository, nombre_corto: str, *, salvo_id: UUID | None = None
) -> None:
    """Chequeo explícito antes del UNIQUE de la DB: un mensaje de dominio claro
    en vez de depender del `IntegrityError` (que queda como red de seguridad)."""
    existente = await repo.get_by_nombre_corto(nombre_corto)
    if existente is not None and existente.id != salvo_id:
        raise PrestadorDuplicadoError(nombre_corto)


class CreatePrestador:
    def __init__(self, ports: ConfigPrestadoresPorts) -> None:
        self._ports = ports

    async def execute(
        self, *, nombre: str, nombre_corto: str, cuit: str | None, region: str | None
    ) -> Prestador:
        normalizado = nombre_corto.strip().upper()
        await _asegurar_nombre_corto_libre(self._ports.prestadores, normalizado)
        return await self._ports.prestadores.create(
            nombre=nombre,
            nombre_corto=normalizado,
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
        normalizado = nombre_corto.strip().upper()
        await _asegurar_nombre_corto_libre(
            self._ports.prestadores, normalizado, salvo_id=prestador_id
        )
        updated = await self._ports.prestadores.update(
            prestador_id, nombre=nombre, nombre_corto=normalizado, cuit=cuit, region=region
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
