import uuid
from datetime import date

from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import ReemplazanteConTurnoSolapadoError
from src.modules.turnos.domain.repositories.asignacion_repository import AsignacionRepository
from src.modules.turnos.domain.repositories.slot_repository import SlotRepository


async def validar_reemplazante_sin_solape(
    slots_repo: SlotRepository | None,
    asigs_repo: AsignacionRepository | None,
    *,
    reemplazante_id: uuid.UUID,
    ausente_id: uuid.UUID,
    desde: date,
    slot_ids: list[uuid.UUID] | None,
) -> None:
    if slots_repo is None or asigs_repo is None:
        return
    todos = await slots_repo.list_all()
    slots_dict = {s.id: s for s in todos}
    cubiertos = await _resolver_slots_cubiertos(
        slots_dict, asigs_repo, ausente_id, desde, slot_ids
    )
    if not cubiertos:
        return
    propios = await _slots_del_reemplazante(slots_dict, asigs_repo, reemplazante_id, desde)
    _detectar_solape_con_propios(cubiertos, propios)


async def _slots_del_reemplazante(
    slots_dict: dict[uuid.UUID, Slot],
    asigs_repo: AsignacionRepository,
    reemplazante_id: uuid.UUID,
    desde: date,
) -> list[Slot]:
    asigs = await asigs_repo.list_by_slots(list(slots_dict.keys()), desde)
    return [
        slots_dict[sid]
        for sid, asig_list in asigs.items()
        if any(a.user_id == reemplazante_id for a in asig_list) and sid in slots_dict
    ]


async def _resolver_slots_cubiertos(
    slots_dict: dict[uuid.UUID, Slot],
    asigs_repo: AsignacionRepository,
    ausente_id: uuid.UUID,
    desde: date,
    slot_ids: list[uuid.UUID] | None,
) -> list[Slot]:
    if slot_ids is not None:
        return [slots_dict[sid] for sid in slot_ids if sid in slots_dict]
    asigs_ausente = await asigs_repo.list_by_slots(list(slots_dict.keys()), desde)
    return [
        slots_dict[sid]
        for sid, asigs in asigs_ausente.items()
        if any(a.user_id == ausente_id for a in asigs) and sid in slots_dict
    ]


def _detectar_solape_con_propios(cubiertos: list[Slot], propios: list[Slot]) -> None:
    for c in cubiertos:
        for p in propios:
            if (
                p.id != c.id
                and p.dia_semana == c.dia_semana
                and p.hora_inicio < c.hora_fin
                and c.hora_inicio < p.hora_fin
            ):
                rango = f"{p.hora_inicio.strftime('%H:%M')}-{p.hora_fin.strftime('%H:%M')}"
                raise ReemplazanteConTurnoSolapadoError(f"{rango} (día {p.dia_semana})")
