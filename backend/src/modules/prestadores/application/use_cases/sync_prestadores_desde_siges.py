from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import SyncResultDTO
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.siges_prestador_gateway import (
    SigesPrestadorGateway,
)


@dataclass(frozen=True, slots=True)
class SyncPrestadoresDesdeSigesDependencies:
    prestadores: PrestadorRepository
    siges: SigesPrestadorGateway


class SyncPrestadoresDesdeSiges:
    """Caso de uso: actualiza `den_comercial`/`razon_social`/`cuit` de los PST
    ya conocidos con el estado actual de Siges. A propósito NO crea PST
    nuevos ni desactiva los que falten en la respuesta — el alta/baja es
    siempre una decisión explícita desde la UI (ver plan: evitar el problema
    del legacy, que creó automáticamente ~29 prestadores fuera de alcance)."""

    def __init__(self, deps: SyncPrestadoresDesdeSigesDependencies) -> None:
        self._deps = deps

    async def execute(self) -> SyncResultDTO:
        existentes = await self._deps.prestadores.list_all(include_inactive=True)
        if not existentes:
            return SyncResultDTO(actualizados=[], sin_cambios=0)

        siges_info = await self._deps.siges.find_by_siges_ids(
            [p.siges_empresa_id for p in existentes]
        )
        por_id = {info.siges_empresa_id: info for info in siges_info}

        actualizados: list[str] = []
        sin_cambios = 0
        for prestador in existentes:
            info = por_id.get(prestador.siges_empresa_id)
            if info is None:
                continue
            if (
                info.den_comercial == prestador.den_comercial
                and info.razon_social == prestador.razon_social
                and info.cuit == prestador.cuit
            ):
                sin_cambios += 1
                continue
            actualizado = Prestador(
                id=prestador.id,
                siges_empresa_id=prestador.siges_empresa_id,
                den_comercial=info.den_comercial,
                razon_social=info.razon_social,
                cuit=info.cuit,
                operador_id=prestador.operador_id,
                is_active=prestador.is_active,
            )
            await self._deps.prestadores.save(actualizado)
            actualizados.append(actualizado.den_comercial)

        return SyncResultDTO(actualizados=actualizados, sin_cambios=sin_cambios)
