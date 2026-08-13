import uuid
from datetime import date

from src.modules.prestadores.application.use_cases.list_asignacion_historial import (
    ListAsignacionHistorial,
    ListAsignacionHistorialDependencies,
)
from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionHistorialRepository,
    FakeUserProvider,
)


def _tramo(
    prestador_id: uuid.UUID, operador_id: uuid.UUID | None, desde: date, hasta: date | None
) -> AsignacionHistorial:
    return AsignacionHistorial(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        operador_id=operador_id,
        desde=desde,
        hasta=hasta,
    )


async def test_ordena_mas_reciente_primero_y_resuelve_nombres() -> None:
    asignaciones = FakeAsignacionHistorialRepository()
    users = FakeUserProvider()
    prestador_id = uuid.uuid4()
    operador_id = uuid.uuid4()
    users.users[operador_id] = UserInfo(id=operador_id, full_name="Ana Pérez")

    viejo = _tramo(prestador_id, operador_id, date(2025, 1, 1), date(2025, 12, 31))
    sin_operador = _tramo(prestador_id, None, date(2026, 1, 1), None)
    asignaciones.rows[viejo.id] = viejo
    asignaciones.rows[sin_operador.id] = sin_operador

    deps = ListAsignacionHistorialDependencies(asignaciones=asignaciones, users=users)
    tramos = await ListAsignacionHistorial(deps).execute(prestador_id)

    assert [t.desde for t in tramos] == [date(2026, 1, 1), date(2025, 1, 1)]
    assert tramos[0].operador_nombre is None
    assert tramos[1].operador_nombre == "Ana Pérez"


async def test_prestador_sin_historial_devuelve_lista_vacia() -> None:
    deps = ListAsignacionHistorialDependencies(
        asignaciones=FakeAsignacionHistorialRepository(), users=FakeUserProvider()
    )
    assert await ListAsignacionHistorial(deps).execute(uuid.uuid4()) == []
