"""Ciclos anuales: listado, apertura del próximo año y saldo con permisos."""

import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.vacaciones.application.use_cases.gestionar_ciclos import (
    AbrirCiclosProximoAnio,
    CiclosDependencies,
    ListarCiclos,
    ObtenerSaldoEmpleado,
)
from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    OperacionNoPermitidaError,
)
from tests.unit.application.vacaciones.fakes import (
    FakeCicloRepo,
    FakeConfigRepo,
    FakeEmpleadoRepo,
    FakeSolicitudRepo,
    FixedClock,
)
from tests.unit.domain.vacaciones.factories import make_actor, make_config, make_empleado

_HOY = date(2026, 8, 14)


def _ciclo(empleado_id: uuid.UUID, year: int, *, is_open: bool = True) -> Ciclo:
    return Ciclo(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        year=year,
        annual_days=14,
        carry_over=0,
        is_open=is_open,
        opened_at=datetime.now(UTC),
    )


def _deps(empleados: FakeEmpleadoRepo, ciclos: FakeCicloRepo) -> CiclosDependencies:
    return CiclosDependencies(
        ciclos=ciclos,
        empleados=empleados,
        solicitudes=FakeSolicitudRepo(),
        config=FakeConfigRepo(make_config()),
        clock=FixedClock(_HOY),
    )


async def test_listar_ciclos_resuelve_el_nombre_del_empleado() -> None:
    empleado = make_empleado()
    ciclos = FakeCicloRepo([_ciclo(empleado.id, 2026), _ciclo(uuid.uuid4(), 2026)])
    deps = _deps(FakeEmpleadoRepo([empleado]), ciclos)

    listado = await ListarCiclos(deps).execute(2026)

    nombres = {d.empleado_nombre for d in listado}
    assert empleado.nombre_completo in nombres
    assert "" in nombres  # el empleado borrado queda con nombre vacío


async def test_abrir_ciclos_crea_saltea_abiertos_y_reabre_cerrados() -> None:
    sin_ciclo = make_empleado(email="a@canal.com")
    ya_abierto = make_empleado(email="b@canal.com")
    cerrado = make_empleado(email="c@canal.com")
    inactivo = make_empleado(email="d@canal.com", status=EstadoEmpleado.INACTIVE)
    ciclos = FakeCicloRepo(
        [_ciclo(ya_abierto.id, 2027), _ciclo(cerrado.id, 2027, is_open=False)]
    )
    deps = _deps(FakeEmpleadoRepo([sin_ciclo, ya_abierto, cerrado, inactivo]), ciclos)

    resultado = await AbrirCiclosProximoAnio(deps).execute()

    assert (resultado.opened, resultado.skipped) == (2, 1)
    nuevo = await ciclos.get(sin_ciclo.id, 2027)
    assert nuevo is not None and nuevo.is_open
    reabierto = await ciclos.get(cerrado.id, 2027)
    assert reabierto is not None and reabierto.is_open
    assert await ciclos.get(inactivo.id, 2027) is None


async def test_obtener_saldo_controla_el_acceso() -> None:
    empleado = make_empleado()
    deps = _deps(FakeEmpleadoRepo([empleado]), FakeCicloRepo([_ciclo(empleado.id, 2026)]))
    caso = ObtenerSaldoEmpleado(deps)

    propio = await caso.execute(empleado.id, 2026, make_actor(empleado_id=empleado.id))
    assert propio.annual == 14

    admin = await caso.execute(empleado.id, 2026, make_actor(es_admin=True))
    assert admin.annual == 14

    jefe = make_actor(sector_gestionado_id=empleado.department_id)
    assert (await caso.execute(empleado.id, 2026, jefe)).annual == 14

    with pytest.raises(OperacionNoPermitidaError):
        await caso.execute(empleado.id, 2026, make_actor(empleado_id=uuid.uuid4()))
    with pytest.raises(EmpleadoNoEncontradoError):
        await caso.execute(uuid.uuid4(), 2026, make_actor(es_admin=True))
