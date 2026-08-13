"""Casos de uso de escritura de Tarifarios — port de POST/PATCH/DELETE /tarifarios.

Toda alta/edición/baja recalcula la cadena temporal de vigencias del grupo
(prestador, tipo_servicio, zona) afectado — ver `domain/services/cadena_tarifaria.py`
(port de `_rebuild_temporal_chain` legacy). Si la edición mueve el tarifario de
grupo, se recadenean el grupo de origen y el de destino. Tras recadenar se relee la
fila (la cadena puede haberle pisado `vigencia_hasta`)."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.errors import TarifarioNoEncontradoError
from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.domain.services.cadena_tarifaria import recalcular_cadena


@dataclass(frozen=True)
class ConfigTarifariosPorts:
    tarifarios: TarifarioRepository


async def _recadenar_grupo_de(repo: TarifarioRepository, t: Tarifario) -> None:
    grupo = await repo.list_grupo(
        prestador_id=t.prestador_id, tipo_servicio=t.tipo_servicio, zona=t.zona
    )
    for ajuste in recalcular_cadena(grupo):
        await repo.set_vigencia_hasta(ajuste.tarifario_id, ajuste.vigencia_hasta)


class CreateTarifario:
    def __init__(self, ports: ConfigTarifariosPorts) -> None:
        self._ports = ports

    async def execute(
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
        repo = self._ports.tarifarios
        creado = await repo.create(
            prestador_id=prestador_id,
            tipo_servicio=tipo_servicio,
            zona=zona,
            costo_servicio=costo_servicio,
            costo_km=costo_km,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=vigencia_hasta,
        )
        await _recadenar_grupo_de(repo, creado)
        refrescado = await repo.get_by_id(creado.id)
        return refrescado or creado


class UpdateTarifario:
    def __init__(self, ports: ConfigTarifariosPorts) -> None:
        self._ports = ports

    async def execute(
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
    ) -> Tarifario:
        repo = self._ports.tarifarios
        anterior = await repo.get_by_id(tarifario_id)
        if anterior is None:
            raise TarifarioNoEncontradoError(tarifario_id)
        updated = await repo.update(
            tarifario_id,
            prestador_id=prestador_id,
            tipo_servicio=tipo_servicio,
            zona=zona,
            costo_servicio=costo_servicio,
            costo_km=costo_km,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=vigencia_hasta,
        )
        if updated is None:
            raise TarifarioNoEncontradoError(tarifario_id)
        await self._recadenar_afectados(anterior, updated)
        refrescado = await repo.get_by_id(tarifario_id)
        return refrescado or updated

    async def _recadenar_afectados(self, anterior: Tarifario, updated: Tarifario) -> None:
        await _recadenar_grupo_de(self._ports.tarifarios, anterior)
        if (updated.prestador_id, updated.tipo_servicio, updated.zona) != (
            anterior.prestador_id,
            anterior.tipo_servicio,
            anterior.zona,
        ):
            await _recadenar_grupo_de(self._ports.tarifarios, updated)


class DeleteTarifario:
    def __init__(self, ports: ConfigTarifariosPorts) -> None:
        self._ports = ports

    async def execute(self, tarifario_id: UUID) -> None:
        repo = self._ports.tarifarios
        anterior = await repo.get_by_id(tarifario_id)
        if anterior is None or not await repo.delete(tarifario_id):
            raise TarifarioNoEncontradoError(tarifario_id)
        await _recadenar_grupo_de(repo, anterior)
