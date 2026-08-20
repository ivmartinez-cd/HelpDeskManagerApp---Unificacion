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
    resolver -- punto de partida del editor del modo vacaciones. También
    advierte qué otros operadores titulares tienen vacaciones aprobadas dentro
    del rango, para que el editor los marque como no disponibles."""

    def __init__(self, deps: PrecargarGrillaVarianteDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, ausente_user_id: uuid.UUID, desde: date, hasta: date
    ) -> PrecargaGrillaDTO:
        validar_vigencia(desde, hasta)
        base = self._deps.base
        casillas, slots, asignaciones = await self._cargar_titular(desde)
        user_ids = {a.user_id for asigs in asignaciones.values() for a in asigs}
        users = await base.users.get_users_by_ids(list(user_ids | {ausente_user_id}))
        ausencias = await base.ausencias.ausencias_aprobadas_en(
            [u for u in user_ids if u != ausente_user_id], desde, hasta
        )
        ctx = _Contexto(ausente_user_id=ausente_user_id, users=users)
        return PrecargaGrillaDTO(
            ausente_user_id=ausente_user_id,
            ausente_nombre=ctx.nombre(ausente_user_id),
            desde=desde,
            hasta=hasta,
            slots=[ctx.slot(s, casillas[s.casilla_id], asignaciones.get(s.id, [])) for s in slots],
            advertencias=[ctx.ausencia(a) for a in ausencias],
        )

    async def _cargar_titular(
        self, fecha: date
    ) -> tuple[dict[uuid.UUID, str], list[Slot], dict[uuid.UUID, list[Asignacion]]]:
        """Casillas activas (id → nombre), sus franjas ordenadas como en el
        admin y las asignaciones vigentes en `fecha` (inicio del rango)."""
        base = self._deps.base
        casillas = {c.id: c for c in await base.casillas.list_all(include_inactive=False)}
        slots = [s for s in await base.slots.list_all() if s.casilla_id in casillas]
        slots.sort(key=lambda s: (casillas[s.casilla_id].sort_order, s.dia_semana, s.hora_inicio))
        asignaciones = await self._deps.asignaciones.list_by_slots([s.id for s in slots], fecha)
        return {cid: c.nombre for cid, c in casillas.items()}, slots, asignaciones


@dataclass(frozen=True, slots=True)
class _Contexto:
    ausente_user_id: uuid.UUID
    users: dict[uuid.UUID, UserInfo]

    def nombre(self, user_id: uuid.UUID) -> str | None:
        info = self.users.get(user_id)
        return info.full_name if info else None

    def slot(
        self, slot: Slot, casilla_nombre: str, asignaciones: list[Asignacion]
    ) -> PrecargaSlotDTO:
        titulares = list(dict.fromkeys(a.user_id for a in asignaciones))
        return PrecargaSlotDTO(
            casilla_id=slot.casilla_id,
            casilla_nombre=casilla_nombre,
            dia_semana=slot.dia_semana,
            hora_inicio=slot.hora_inicio,
            hora_fin=slot.hora_fin,
            sort_order=slot.sort_order,
            operadores=[
                operator_view(u, self.users) for u in titulares if u != self.ausente_user_id
            ],
            requiere_cobertura=self.ausente_user_id in titulares,
        )

    def ausencia(self, a: AusenciaAprobada) -> AdvertenciaCoberturaDTO:
        return AdvertenciaCoberturaDTO(
            tipo="OPERADOR_AUSENTE",
            user_id=a.user_id,
            user_name=self.nombre(a.user_id),
            desde=a.desde,
            hasta=a.hasta,
        )
