import uuid
from datetime import date

from src.modules.prestadores.application.dtos.prestador_dtos import AssignOperadorCommand
from src.modules.prestadores.application.use_cases.assign_operador import (
    AssignOperador,
    AssignOperadorDependencies,
)
from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.entities.prestador import Prestador
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionHistorialRepository,
    FakeContactoRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)


def _deps(
    prestadores: FakePrestadorRepository, asignaciones: FakeAsignacionHistorialRepository
) -> AssignOperadorDependencies:
    return AssignOperadorDependencies(
        prestadores=prestadores,
        asignaciones=asignaciones,
        contactos=FakeContactoRepository(),
        users=FakeUserProvider(),
    )


async def test_reasignar_actualiza_el_puntero_y_cierra_el_tramo_anterior() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()

    operador_viejo = uuid.uuid4()
    operador_nuevo = uuid.uuid4()
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Rosario",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=operador_viejo,
        is_active=True,
    )
    prestadores.rows[prestador.id] = prestador
    tramo_abierto = AsignacionHistorial(
        id=uuid.uuid4(),
        prestador_id=prestador.id,
        operador_id=operador_viejo,
        desde=date(2025, 9, 4),
        hasta=None,
    )
    asignaciones.rows[tramo_abierto.id] = tramo_abierto

    use_case = AssignOperador(_deps(prestadores, asignaciones))
    dto = await use_case.execute(
        AssignOperadorCommand(
            prestador_id=prestador.id, operador_id=operador_nuevo, desde=date(2026, 8, 12)
        )
    )

    assert dto.operador_id == operador_nuevo
    assert prestadores.rows[prestador.id].operador_id == operador_nuevo

    tramos = list(asignaciones.rows.values())
    cerrado = next(t for t in tramos if t.operador_id == operador_viejo)
    abierto = next(t for t in tramos if t.operador_id == operador_nuevo)
    assert cerrado.hasta == date(2026, 8, 11)
    assert abierto.hasta is None
    assert abierto.desde == date(2026, 8, 12)


async def test_desasignar_deja_operador_id_en_none() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    operador = uuid.uuid4()
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Esquel",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=operador,
        is_active=True,
    )
    prestadores.rows[prestador.id] = prestador

    use_case = AssignOperador(_deps(prestadores, asignaciones))
    dto = await use_case.execute(
        AssignOperadorCommand(prestador_id=prestador.id, operador_id=None, desde=date(2026, 8, 12))
    )

    assert dto.operador_id is None
    assert prestadores.rows[prestador.id].operador_id is None
