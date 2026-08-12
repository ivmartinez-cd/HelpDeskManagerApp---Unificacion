import uuid
from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import (
    OperadorGroupDTO,
    PrestadorDTO,
    PrestadoresResumenDTO,
)
from src.modules.prestadores.application.use_cases.prestador_dto_builder import (
    build_prestador_dto,
)
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class ListPrestadoresAgrupadosDependencies:
    prestadores: PrestadorRepository
    contactos: ContactoRepository
    users: UserProvider


class ListPrestadoresAgrupados:
    """Caso de uso: el directorio de PST agrupado por operador asignado, con
    el resumen que alimenta los KPI tiles."""

    def __init__(self, deps: ListPrestadoresAgrupadosDependencies) -> None:
        self._deps = deps

    async def execute(self, *, include_inactive: bool = True) -> PrestadoresResumenDTO:
        prestadores = await self._deps.prestadores.list_all(include_inactive=include_inactive)
        contactos_por_prestador = await self._deps.contactos.list_by_prestadores(
            [p.id for p in prestadores]
        )
        operador_ids = {p.operador_id for p in prestadores if p.operador_id is not None}
        users = await self._deps.users.get_users_by_ids(list(operador_ids))

        dtos = [
            build_prestador_dto(p, contactos_por_prestador.get(p.id, []), users)
            for p in prestadores
        ]

        grouped: dict[uuid.UUID | None, list[PrestadorDTO]] = {}
        for dto in dtos:
            grouped.setdefault(dto.operador_id, []).append(dto)

        grupos = [
            OperadorGroupDTO(
                operador_id=operador_id,
                operador_nombre=users[operador_id].full_name if operador_id in users else None,
                operador_color=users[operador_id].color if operador_id in users else None,
                prestadores=sorted(items, key=lambda d: d.den_comercial),
            )
            for operador_id, items in grouped.items()
            if operador_id is not None
        ]
        grupos.sort(key=lambda g: g.operador_nombre or "")

        sin_asignar_items = grouped.get(None, [])
        if sin_asignar_items:
            grupos.append(
                OperadorGroupDTO(
                    operador_id=None,
                    operador_nombre=None,
                    operador_color=None,
                    prestadores=sorted(sin_asignar_items, key=lambda d: d.den_comercial),
                )
            )

        activos = [p for p in prestadores if p.is_active]
        return PrestadoresResumenDTO(
            total_prestadores=len(prestadores),
            total_activos=len(activos),
            operadores_con_pst=len({p.operador_id for p in activos if p.operador_id is not None}),
            sin_asignar=len([p for p in activos if p.operador_id is None]),
            grupos=grupos,
        )
