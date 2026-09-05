"""Casos de uso de escritura del catálogo de SPSTs — port de
POST/PATCH/DELETE /spsts."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.errors import SpstNoEncontradoError
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository


@dataclass(frozen=True)
class ConfigSpstsPorts:
    spsts: SpstRepository


class CreateSpst:
    def __init__(self, ports: ConfigSpstsPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        *,
        prestador_id: UUID,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona_cobertura: str | None,
    ) -> Spst:
        return await self._ports.spsts.create(
            prestador_id=prestador_id,
            nombre=nombre,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            zona_cobertura=zona_cobertura,
        )


class UpdateSpst:
    def __init__(self, ports: ConfigSpstsPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        spst_id: UUID,
        *,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona_cobertura: str | None,
    ) -> Spst:
        updated = await self._ports.spsts.update(
            spst_id,
            nombre=nombre,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            zona_cobertura=zona_cobertura,
        )
        if updated is None:
            raise SpstNoEncontradoError(spst_id)
        return updated


class ToggleSpstActivo:
    def __init__(self, ports: ConfigSpstsPorts) -> None:
        self._ports = ports

    async def execute(self, spst_id: UUID, *, activo: bool) -> Spst:
        updated = await self._ports.spsts.toggle_activo(spst_id, activo=activo)
        if updated is None:
            raise SpstNoEncontradoError(spst_id)
        return updated


class DeleteSpst:
    def __init__(self, ports: ConfigSpstsPorts) -> None:
        self._ports = ports

    async def execute(self, spst_id: UUID) -> None:
        if not await self._ports.spsts.delete(spst_id):
            raise SpstNoEncontradoError(spst_id)
