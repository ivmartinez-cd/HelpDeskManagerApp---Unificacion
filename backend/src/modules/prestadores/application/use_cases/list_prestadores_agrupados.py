import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.prestadores.application.dtos.prestador_dtos import (
    OperadorGroupDTO,
    PrestadorDTO,
    PrestadoresResumenDTO,
)
from src.modules.prestadores.application.use_cases.prestador_dto_builder import (
    build_prestador_dto,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.prestadores.domain.repositories.contacto_repository import ContactoRepository
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserInfo, UserProvider
from src.modules.prestadores.domain.services.operador_efectivo import resolver_operador_efectivo


@dataclass(frozen=True, slots=True)
class ListPrestadoresAgrupadosDependencies:
    prestadores: PrestadorRepository
    contactos: ContactoRepository
    users: UserProvider
    overrides: AsignacionOverrideRepository


class ListPrestadoresAgrupados:
    """Caso de uso: el directorio de PST agrupado por operador *efectivo* a
    la fecha de consulta (default hoy) — un PST cubierto por un override
    vigente aparece agrupado bajo el reemplazante, no bajo el titular
    permanente (ver ADR-013). Cada `PrestadorDTO` sigue mostrando su
    asignación real (`Prestador.operador_id`), solo el agrupado cambia."""

    def __init__(self, deps: ListPrestadoresAgrupadosDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, include_inactive: bool = True, fecha: date | None = None
    ) -> PrestadoresResumenDTO:
        prestadores = await self._deps.prestadores.list_all(include_inactive=include_inactive)
        contactos_por_prestador = await self._deps.contactos.list_by_prestadores(
            [p.id for p in prestadores]
        )
        efectivo_por_prestador = await self._resolver_efectivos(prestadores, fecha or date.today())

        operador_ids = {p.operador_id for p in prestadores if p.operador_id is not None}
        operador_ids |= {v for v in efectivo_por_prestador.values() if v is not None}
        users = await self._deps.users.get_users_by_ids(list(operador_ids))

        dtos = [
            build_prestador_dto(p, contactos_por_prestador.get(p.id, []), users)
            for p in prestadores
        ]

        activos = [p for p in prestadores if p.is_active]
        return PrestadoresResumenDTO(
            total_prestadores=len(prestadores),
            total_activos=len(activos),
            operadores_con_pst=len({p.operador_id for p in activos if p.operador_id is not None}),
            sin_asignar=len([p for p in activos if p.operador_id is None]),
            grupos=_agrupar(dtos, efectivo_por_prestador, users),
        )

    async def _resolver_efectivos(
        self, prestadores: list[Prestador], fecha: date
    ) -> dict[uuid.UUID, uuid.UUID | None]:
        operador_ids = {p.operador_id for p in prestadores if p.operador_id is not None}
        overrides_por_ausente = {
            operador_id: await self._deps.overrides.list_activos_por_ausente(operador_id)
            for operador_id in operador_ids
        }
        return {
            p.id: resolver_operador_efectivo(
                p.operador_id,
                p.id,
                fecha,
                overrides_por_ausente.get(p.operador_id, []) if p.operador_id else [],
            )
            for p in prestadores
        }


def _agrupar(
    dtos: list[PrestadorDTO],
    efectivo_por_prestador: dict[uuid.UUID, uuid.UUID | None],
    users: dict[uuid.UUID, UserInfo],
) -> list[OperadorGroupDTO]:
    grouped: dict[uuid.UUID | None, list[PrestadorDTO]] = {}
    for dto in dtos:
        grouped.setdefault(efectivo_por_prestador[dto.id], []).append(dto)

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
    return grupos
