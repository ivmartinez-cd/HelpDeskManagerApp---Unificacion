import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    AdvertenciaCoberturaDTO,
    PrecargaGrillaDTO,
    PrecargaSlotDTO,
)
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
    operator_view,
)
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.ausencias_lookup import AusenciaAprobada
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from src.modules.turnos.domain.services.grilla_variante_reglas import validar_vigencia


@dataclass(frozen=True, slots=True)
class PrecargarGrillaVarianteDependencies:
    base: GrillaVarianteDependencies
    asignaciones: AsignacionRepository


class PrecargarGrillaVariante:
    """Caso de uso (solo lectura, no persiste): la grilla titular vigente al
    inicio del rango con las franjas del ausente marcadas como huecos a
    resolver -- punto de partida del editor de grilla variante. Si no hay
    ausente, precarga la titular completa para ajustes puntuales."""

    def __init__(self, deps: PrecargarGrillaVarianteDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, ausente_user_id: uuid.UUID | None = None, desde: date, hasta: date
    ) -> PrecargaGrillaDTO:
        validar_vigencia(desde, hasta)
        casillas, slots, asignaciones = await self._cargar_titular(desde)
        user_ids = {a.user_id for asigs in asignaciones.values() for a in asigs}
        users = await self._cargar_usuarios(user_ids, ausente_user_id)
        ausencias = await self._cargar_ausencias(user_ids, ausente_user_id, desde, hasta)
        ctx = _Contexto(ausente_user_id=ausente_user_id, users=users)
        return PrecargaGrillaDTO(
            ausente_user_id=ausente_user_id,
            ausente_nombre=ctx.nombre(ausente_user_id) if ausente_user_id else None,
            desde=desde,
            hasta=hasta,
            slots=[ctx.slot(s, casillas[s.casilla_id], asignaciones.get(s.id, [])) for s in slots],
            advertencias=[ctx.ausencia(a) for a in ausencias if a.impide_cobertura],
        )

    async def _cargar_usuarios(
        self, user_ids: set[uuid.UUID], ausente_id: uuid.UUID | None
    ) -> dict[uuid.UUID, UserInfo]:
        query_ids = list(user_ids | ({ausente_id} if ausente_id else set()))
        return await self._deps.base.users.get_users_by_ids(query_ids)

    async def _cargar_ausencias(
        self, user_ids: set[uuid.UUID], ausente_id: uuid.UUID | None, desde: date, hasta: date
    ) -> list[AusenciaAprobada]:
        if ausente_id is None:
            return []
        return await self._deps.base.ausencias.ausencias_aprobadas_en(
            [u for u in user_ids if u != ausente_id], desde, hasta
        )

    async def _cargar_titular(
        self, fecha: date
    ) -> tuple[dict[uuid.UUID, str], list[Slot], dict[uuid.UUID, list[Asignacion]]]:
        base = self._deps.base
        casillas = {c.id: c for c in await base.casillas.list_all(include_inactive=False)}
        slots = [s for s in await base.slots.list_all() if s.casilla_id in casillas]
        slots.sort(key=lambda s: (casillas[s.casilla_id].sort_order, s.dia_semana, s.hora_inicio))
        asignaciones = await self._deps.asignaciones.list_by_slots([s.id for s in slots], fecha)
        return {cid: c.nombre for cid, c in casillas.items()}, slots, asignaciones


@dataclass(frozen=True, slots=True)
class _Contexto:
    ausente_user_id: uuid.UUID | None
    users: dict[uuid.UUID, UserInfo]

    def nombre(self, user_id: uuid.UUID) -> str | None:
        info = self.users.get(user_id)
        return info.full_name if info else None

    def slot(
        self, slot: Slot, casilla_nombre: str, asignaciones: list[Asignacion]
    ) -> PrecargaSlotDTO:
        titulares = list(dict.fromkeys(a.user_id for a in asignaciones))
        operadores = (
            [operator_view(u, self.users) for u in titulares if u != self.ausente_user_id]
            if self.ausente_user_id is not None
            else [operator_view(u, self.users) for u in titulares]
        )
        requiere = bool(self.ausente_user_id is not None and self.ausente_user_id in titulares)
        return PrecargaSlotDTO(
            casilla_id=slot.casilla_id,
            casilla_nombre=casilla_nombre,
            dia_semana=slot.dia_semana,
            hora_inicio=slot.hora_inicio,
            hora_fin=slot.hora_fin,
            sort_order=slot.sort_order,
            operadores=operadores,
            requiere_cobertura=requiere,
        )

    def ausencia(self, a: AusenciaAprobada) -> AdvertenciaCoberturaDTO:
        return AdvertenciaCoberturaDTO(
            tipo="OPERADOR_AUSENTE",
            user_id=a.user_id,
            user_name=self.nombre(a.user_id),
            desde=a.desde,
            hasta=a.hasta,
            detalle=a.detalle,
        )
