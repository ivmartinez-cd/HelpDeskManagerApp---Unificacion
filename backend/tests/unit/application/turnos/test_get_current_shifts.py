import uuid
from datetime import datetime, time
from zoneinfo import ZoneInfo

from src.modules.turnos.application.use_cases.get_current_shifts import (
    GetCurrentShifts,
    GetCurrentShiftsDependencies,
)
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionOverrideRepository,
    FakeAsignacionRepository,
    FakeCasillaRepository,
    FakeSlotRepository,
    FakeUserProvider,
)

_ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


async def test_muestra_al_reemplazante_cuando_hay_una_cobertura_activa() -> None:
    casilla = Casilla(id=uuid.uuid4(), nombre="INSUMOS", color=None, sort_order=0, is_active=True)
    # 2026-08-25 es martes (dia_semana=1)
    slot = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla.id,
        hora_inicio=time(8, 0),
        hora_fin=time(11, 0),
        dia_semana=1,
        sort_order=0,
    )
    ausente, reemplazante = uuid.uuid4(), uuid.uuid4()

    casillas_repo = FakeCasillaRepository()
    casillas_repo.rows[casilla.id] = casilla
    slots_repo = FakeSlotRepository()
    slots_repo.rows[slot.id] = slot
    asignaciones_repo = FakeAsignacionRepository()
    asignaciones_repo.rows[uuid.uuid4()] = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot.id,
        user_id=ausente,
        vigente_desde=datetime(2026, 1, 1).date(),
        vigente_hasta=None,
    )
    overrides_repo = FakeAsignacionOverrideRepository()
    cobertura: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=datetime(2026, 8, 24).date(),
        hasta=datetime(2026, 8, 28).date(),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo="vacaciones",
        created_by_user_id=uuid.uuid4(),
    )
    overrides_repo.rows[cobertura.id] = cobertura
    users_repo = FakeUserProvider()
    users_repo.users[reemplazante] = UserInfo(id=reemplazante, full_name="Luna Torres")

    use_case = GetCurrentShifts(
        GetCurrentShiftsDependencies(
            casillas=casillas_repo,
            slots=slots_repo,
            asignaciones=asignaciones_repo,
            users=users_repo,
            overrides=overrides_repo,
        )
    )
    result = await use_case.execute(
        now_datetime=datetime(2026, 8, 25, 9, 0, tzinfo=_ARGENTINA_TZ)
    )

    assert len(result) == 1
    assert [op.user_id for op in result[0].operadores] == [reemplazante]
    assert result[0].operadores[0].user_name == "Luna Torres"
