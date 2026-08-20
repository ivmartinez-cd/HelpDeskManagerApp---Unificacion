"""Test de aceptación del caso real (ADR-025 / PLAN_COBERTURA_VACACIONES_MAJO):
dada la grilla titular y la variante cargada, `/current` de un miércoles dentro
de la vigencia devuelve exactamente la grilla esperada con el badge de
variante; el miércoles siguiente (vencida), la titular sin badge -- sin que
nadie toque nada."""

import uuid
from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    CreateGrillaVarianteCommand,
    CurrentShiftsDTO,
    VarianteSlotInput,
)
from src.modules.turnos.application.use_cases.create_grilla_variante import (
    CreateGrillaVariante,
)
from src.modules.turnos.application.use_cases.get_current_shifts import (
    GetCurrentShifts,
    GetCurrentShiftsDependencies,
)
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
)
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.unit.domain.turnos.caso_majo import (
    LUNES_VUELTA,
    MIERCOLES_DENTRO,
    MIERCOLES_SIGUIENTE,
    VIGENCIA_DESDE,
    VIGENCIA_HASTA,
    CasoMajo,
)
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionOverrideRepository,
    FakeAsignacionRepository,
    FakeCasillaRepository,
    FakeGrillaVarianteRepository,
    FakeSlotRepository,
    FakeUserProvider,
)

_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def _armar(caso: CasoMajo) -> tuple[GrillaVarianteDependencies, GetCurrentShiftsDependencies]:
    casillas = FakeCasillaRepository()
    slots = FakeSlotRepository()
    asignaciones = FakeAsignacionRepository()
    users = FakeUserProvider()
    variantes = FakeGrillaVarianteRepository()
    for c in caso.casillas:
        casillas.rows[c.id] = c
    for s in caso.slots:
        slots.rows[s.id] = s
    for a in caso.asignaciones:
        asignaciones.rows[a.id] = a
    for uid, nombre in caso.nombres.items():
        users.users[uid] = UserInfo(id=uid, full_name=nombre)
    return (
        GrillaVarianteDependencies(
            variantes=variantes, casillas=casillas, slots=slots, users=users
        ),
        GetCurrentShiftsDependencies(
            casillas=casillas,
            slots=slots,
            asignaciones=asignaciones,
            users=users,
            overrides=FakeAsignacionOverrideRepository(),
            variantes=variantes,
        ),
    )


def _command_variante(caso: CasoMajo) -> CreateGrillaVarianteCommand:
    esperada = caso.variante_esperada()
    return CreateGrillaVarianteCommand(
        motivo=esperada.motivo,
        origen_texto=esperada.origen_texto,
        desde=VIGENCIA_DESDE,
        hasta=VIGENCIA_HASTA,
        slots=[
            VarianteSlotInput(
                casilla_id=s.casilla_id,
                dia_semana=s.dia_semana,
                hora_inicio=s.hora_inicio,
                hora_fin=s.hora_fin,
                user_ids=s.user_ids,
            )
            for s in esperada.slots
        ],
        created_by_user_id=uuid.uuid4(),
    )


def _grilla(result: CurrentShiftsDTO) -> list[tuple[str, str, str, list[str]]]:
    return [
        (
            s.casilla_nombre,
            s.hora_inicio.strftime("%H:%M"),
            s.hora_fin.strftime("%H:%M"),
            [o.user_name for o in s.operadores],
        )
        for s in result.shifts
    ]


async def test_caso_majo_variante_vigente_y_vuelta_automatica_a_la_titular() -> None:
    caso = CasoMajo()
    deps_variante, deps_current = _armar(caso)
    creada = await CreateGrillaVariante(deps_variante).execute(_command_variante(caso))
    assert [a.tipo for a in creada.advertencias] == ["HUECO"] * 5  # INSUMOS 8:00-8:30, L-V

    dentro = await GetCurrentShifts(deps_current).execute(
        now_datetime=datetime.combine(MIERCOLES_DENTRO, time(10), tzinfo=_TZ)
    )
    assert dentro.variante_activa is not None
    assert (dentro.variante_activa.motivo, dentro.variante_activa.hasta) == (
        "Vacaciones M. J. Vela",
        VIGENCIA_HASTA,
    )
    assert _grilla(dentro) == [
        ("INSUMOS", "08:30", "11:00", ["Mariano Gomez"]),
        ("INSUMOS", "11:00", "13:00", ["Luna Torres"]),
        ("INSUMOS", "13:00", "17:00", ["Mariano Gomez"]),
        ("INSUMOS", "17:00", "18:00", ["Victor Paez"]),
        ("ST", "08:00", "09:00", ["Mariana Rodriguez"]),
        ("ST", "09:00", "14:00", ["Victor Paez"]),
        ("ST", "14:00", "18:00", ["Luna Torres"]),
    ]
    assert not any("Maria Jose Vela" in ops for *_, ops in _grilla(dentro))

    for fecha in (LUNES_VUELTA, MIERCOLES_SIGUIENTE):
        fuera = await GetCurrentShifts(deps_current).execute(
            now_datetime=datetime.combine(fecha, time(8, 5), tzinfo=_TZ)
        )
        assert fuera.variante_activa is None
        assert _grilla(fuera) == [
            ("INSUMOS", "08:00", "11:00", ["Maria Jose Vela"]),
            ("INSUMOS", "11:00", "13:00", ["Luna Torres"]),
            ("INSUMOS", "13:00", "17:00", ["Mariano Gomez"]),
            ("INSUMOS", "17:00", "18:00", ["Victor Paez"]),
            ("ST", "09:00", "13:00", ["Victor Paez"]),
            ("ST", "13:00", "15:00", ["Maria Jose Vela"]),
            ("ST", "15:00", "18:00", ["Luna Torres"]),
        ]
