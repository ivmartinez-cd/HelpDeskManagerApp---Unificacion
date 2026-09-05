"""Piezas compartidas por los casos de uso de grilla variante (ADR-025):
dependencias, construcción de la entidad desde el command, validación +
advertencias y armado del DTO con nombres resueltos."""

import uuid
from dataclasses import dataclass, field

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    AdvertenciaCoberturaDTO,
    GrillaVarianteDTO,
    VarianteSlotDTO,
    VarianteSlotInput,
)
from src.modules.turnos.application.dtos.turno_dtos import OperatorShiftView
from src.modules.turnos.application.use_cases.usuarios_support import validar_usuarios_existen
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante, VarianteSlot
from src.modules.turnos.domain.errors import OverlappingVarianteError, VarianteCasillaInvalidaError
from src.modules.turnos.domain.repositories.ausencias_lookup import (
    AusenciasLookup,
    AusenciasLookupNulo,
)
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository
from src.modules.turnos.domain.repositories.grilla_variante_repository import (
    GrillaVarianteRepository,
)
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository
from src.modules.turnos.domain.repositories.user_provider import UserInfo, UserProvider
from src.modules.turnos.domain.services.grilla_variante_reglas import (
    AdvertenciaCobertura,
    advertencias_de_cobertura,
    hay_solapamiento_vigencia,
    validar_franjas,
    validar_vigencia,
)


@dataclass(frozen=True, slots=True)
class GrillaVarianteDependencies:
    variantes: GrillaVarianteRepository
    casillas: CasillaRepository
    slots: SlotRepository
    users: UserProvider
    ausencias: AusenciasLookup = field(default_factory=AusenciasLookupNulo)


def build_variante_slots(inputs: list[VarianteSlotInput]) -> list[VarianteSlot]:
    """Ids nuevos siempre (también al editar: la edición reemplaza las franjas
    completas, ver repositorio); `sort_order` = posición en el payload."""
    return [
        VarianteSlot(
            id=uuid.uuid4(),
            casilla_id=i.casilla_id,
            dia_semana=i.dia_semana,
            hora_inicio=i.hora_inicio,
            hora_fin=i.hora_fin,
            sort_order=idx,
            user_ids=list(dict.fromkeys(i.user_ids)),
        )
        for idx, i in enumerate(inputs)
    ]


async def validar_variante(
    deps: GrillaVarianteDependencies,
    variante: GrillaVariante,
    *,
    excluir_id: uuid.UUID | None = None,
) -> None:
    """Invariantes duras (ADR-025). `excluir_id` = la propia variante al editar."""
    validar_vigencia(variante.desde, variante.hasta)
    validar_franjas(variante.slots)
    casillas_validas = {c.id for c in await deps.casillas.list_all(include_inactive=True)}
    if any(s.casilla_id not in casillas_validas for s in variante.slots):
        raise VarianteCasillaInvalidaError()
    await validar_usuarios_existen(deps.users, [u for s in variante.slots for u in s.user_ids])
    existentes = [v for v in await deps.variantes.list_activas() if v.id != excluir_id]
    if hay_solapamiento_vigencia(variante.desde, variante.hasta, existentes):
        raise OverlappingVarianteError()


async def calcular_advertencias(
    deps: GrillaVarianteDependencies, variante: GrillaVariante
) -> list[AdvertenciaCobertura]:
    """Huecos vs. titular + franjas sin operador + cubrientes con vacaciones
    aprobadas solapadas. Nunca bloquea."""
    titulares = await deps.slots.list_all()
    advertencias = advertencias_de_cobertura(variante.slots, titulares)
    user_ids = list({u for s in variante.slots for u in s.user_ids})
    ausencias = await deps.ausencias.ausencias_aprobadas_en(
        user_ids, variante.desde, variante.hasta
    )
    advertencias += [
        AdvertenciaCobertura(
            tipo="OPERADOR_AUSENTE",
            user_id=a.user_id,
            desde=a.desde,
            hasta=a.hasta,
            detalle=a.detalle,
        )
        for a in ausencias
        if a.impide_cobertura  # home office no saca a nadie de la grilla
    ]
    return advertencias


@dataclass(frozen=True, slots=True)
class NombresResueltos:
    casillas: dict[uuid.UUID, str]
    users: dict[uuid.UUID, UserInfo]


async def resolver_nombres(
    deps: GrillaVarianteDependencies,
    variantes: list[GrillaVariante],
    advertencias: list[AdvertenciaCobertura],
) -> NombresResueltos:
    """Una consulta de casillas + una de usuarios para todo el lote (sin N+1)."""
    casillas = {c.id: c.nombre for c in await deps.casillas.list_all(include_inactive=True)}
    user_ids = {u for v in variantes for s in v.slots for u in s.user_ids}
    user_ids |= {a.user_id for a in advertencias if a.user_id is not None}
    users = await deps.users.get_users_by_ids(list(user_ids))
    return NombresResueltos(casillas=casillas, users=users)


async def build_grilla_variante_dto(
    deps: GrillaVarianteDependencies,
    variante: GrillaVariante,
    advertencias: list[AdvertenciaCobertura],
) -> GrillaVarianteDTO:
    nombres = await resolver_nombres(deps, [variante], advertencias)
    return grilla_variante_dto(variante, advertencias, nombres)


def grilla_variante_dto(
    variante: GrillaVariante,
    advertencias: list[AdvertenciaCobertura],
    nombres: NombresResueltos,
) -> GrillaVarianteDTO:
    casillas, users = nombres.casillas, nombres.users
    return GrillaVarianteDTO(
        id=variante.id,
        motivo=variante.motivo,
        origen_texto=variante.origen_texto,
        desde=variante.desde,
        hasta=variante.hasta,
        estado=variante.estado,
        created_by_user_id=variante.created_by_user_id,
        slots=[_slot_dto(s, casillas, users) for s in variante.slots],
        advertencias=[advertencia_dto(a, casillas, users) for a in advertencias],
    )


def _slot_dto(
    slot: VarianteSlot, casillas: dict[uuid.UUID, str], users: dict[uuid.UUID, UserInfo]
) -> VarianteSlotDTO:
    return VarianteSlotDTO(
        id=slot.id,
        casilla_id=slot.casilla_id,
        casilla_nombre=casillas.get(slot.casilla_id, "?"),
        dia_semana=slot.dia_semana,
        hora_inicio=slot.hora_inicio,
        hora_fin=slot.hora_fin,
        sort_order=slot.sort_order,
        operadores=[operator_view(u, users) for u in slot.user_ids],
    )


def operator_view(user_id: uuid.UUID, users: dict[uuid.UUID, UserInfo]) -> OperatorShiftView:
    info = users.get(user_id)
    return OperatorShiftView(
        user_id=user_id,
        user_name=info.full_name if info else "Desconocido",
        color=info.color if info else None,
    )


def advertencia_dto(
    a: AdvertenciaCobertura, casillas: dict[uuid.UUID, str], users: dict[uuid.UUID, UserInfo]
) -> AdvertenciaCoberturaDTO:
    user = users.get(a.user_id) if a.user_id is not None else None
    return AdvertenciaCoberturaDTO(
        tipo=a.tipo,
        casilla_id=a.casilla_id,
        casilla_nombre=casillas.get(a.casilla_id) if a.casilla_id is not None else None,
        dia_semana=a.dia_semana,
        hora_inicio=a.hora_inicio,
        hora_fin=a.hora_fin,
        user_id=a.user_id,
        user_name=user.full_name if user else None,
        desde=a.desde,
        hasta=a.hasta,
        detalle=a.detalle,
    )
