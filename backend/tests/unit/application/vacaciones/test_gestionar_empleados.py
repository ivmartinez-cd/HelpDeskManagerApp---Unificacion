"""ABM de empleados: listados con scoping, unicidad y recálculo de ciclos."""

import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.vacaciones.application.dtos.gestion_dtos import (
    EmpleadoCommand,
    ListEmpleadosQuery,
)
from src.modules.vacaciones.application.use_cases.gestionar_empleados import (
    CreateEmpleado,
    DeleteEmpleado,
    GestionEmpleadosDependencies,
    ListEmpleados,
    UpdateEmpleado,
)
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    NombreDuplicadoError,
)
from src.shared.domain.errors import NotFoundError
from tests.unit.application.vacaciones.fakes import (
    FakeCargoRepo,
    FakeCicloRepo,
    FakeConfigRepo,
    FakeEmpleadoRepo,
    FakeSectorRepo,
    FakeSolicitudRepo,
    FixedClock,
)
from tests.unit.domain.vacaciones.factories import make_actor, make_config, make_empleado

_HOY = date(2026, 8, 14)


def _deps(
    empleados: FakeEmpleadoRepo,
    *,
    sector: Sector,
    cargo: Cargo,
    ciclos: FakeCicloRepo | None = None,
) -> GestionEmpleadosDependencies:
    return GestionEmpleadosDependencies(
        empleados=empleados,
        sectores=FakeSectorRepo([sector]),
        cargos=FakeCargoRepo([cargo]),
        ciclos=ciclos or FakeCicloRepo(),
        config=FakeConfigRepo(make_config()),
        clock=FixedClock(_HOY),
        solicitudes=FakeSolicitudRepo(),
    )


def _sector() -> Sector:
    return Sector(id=uuid.uuid4(), name="Mesa", color="#123", is_active=True)


def _cargo() -> Cargo:
    return Cargo(id=uuid.uuid4(), name="Técnico", max_simultaneos=None)


def _command(sector: Sector, cargo: Cargo, **overrides: object) -> EmpleadoCommand:
    base: dict[str, object] = {
        "first_name": "Laura",
        "last_name": "Pérez",
        "email": "lperez@canal.com",
        "hire_date": date(2019, 3, 15),
        "department_id": sector.id,
        "cargo_id": cargo.id,
        "color": "#2563eb",
        "status": EstadoEmpleado.ACTIVE,
        "user_id": None,
    }
    base.update(overrides)
    return EmpleadoCommand(**base)  # type: ignore[arg-type]


async def test_list_empleados_enriquece_con_sector_cargo_y_antiguedad() -> None:
    sector, cargo = _sector(), _cargo()
    empleado = make_empleado(department_id=sector.id, cargo_id=cargo.id)
    deps = _deps(FakeEmpleadoRepo([empleado]), sector=sector, cargo=cargo)

    items = await ListEmpleados(deps).execute(ListEmpleadosQuery(), make_actor(es_admin=True))

    assert len(items) == 1
    item = items[0]
    assert item.sector_nombre == "Mesa" and item.cargo_nombre == "Técnico"
    # hire 2019-03-15, hoy 2026-08-14 → ~7.4 años → tramo 5-10 → 21 días
    assert item.dias_anuales == 21
    assert 7 < item.antiguedad_anios < 8


async def test_list_empleados_sin_acceso_devuelve_vacio() -> None:
    sector, cargo = _sector(), _cargo()
    deps = _deps(FakeEmpleadoRepo([make_empleado()]), sector=sector, cargo=cargo)

    assert await ListEmpleados(deps).execute(ListEmpleadosQuery(), make_actor()) == []


async def test_create_empleado_valida_referencias_y_unicidad() -> None:
    sector, cargo = _sector(), _cargo()
    empleados = FakeEmpleadoRepo([])
    deps = _deps(empleados, sector=sector, cargo=cargo)

    creado = await CreateEmpleado(deps).execute(_command(sector, cargo))
    assert await empleados.get_by_id(creado.id) is creado

    with pytest.raises(NombreDuplicadoError):
        await CreateEmpleado(deps).execute(_command(sector, cargo))
    with pytest.raises(NotFoundError):
        await CreateEmpleado(deps).execute(
            _command(sector, cargo, email="otra@canal.com", department_id=uuid.uuid4())
        )
    with pytest.raises(NotFoundError):
        await CreateEmpleado(deps).execute(
            _command(sector, cargo, email="otra@canal.com", cargo_id=uuid.uuid4())
        )


async def test_create_empleado_rechaza_user_id_ya_vinculado() -> None:
    sector, cargo = _sector(), _cargo()
    user_id = uuid.uuid4()
    vinculado = make_empleado(user_id=user_id, department_id=sector.id, cargo_id=cargo.id)
    deps = _deps(FakeEmpleadoRepo([vinculado]), sector=sector, cargo=cargo)

    with pytest.raises(NombreDuplicadoError):
        await CreateEmpleado(deps).execute(
            _command(sector, cargo, email="otra@canal.com", user_id=user_id)
        )


async def test_update_empleado_recalcula_ciclos_al_cambiar_hire_date() -> None:
    sector, cargo = _sector(), _cargo()
    empleado = make_empleado(
        hire_date=date(2019, 3, 15), department_id=sector.id, cargo_id=cargo.id
    )
    # Con hire 2019: 2026 cae en el tramo 5-10 (21 días). Con hire 2025: 14.
    ciclo = Ciclo(
        id=uuid.uuid4(),
        empleado_id=empleado.id,
        year=2026,
        annual_days=21,
        carry_over=0,
        is_open=True,
        opened_at=datetime.now(UTC),
    )
    ciclos = FakeCicloRepo([ciclo])
    deps = _deps(FakeEmpleadoRepo([empleado]), sector=sector, cargo=cargo, ciclos=ciclos)

    await UpdateEmpleado(deps).execute(
        empleado.id, _command(sector, cargo, email=empleado.email, hire_date=date(2025, 3, 15))
    )

    assert ciclo.annual_days == 14
    assert ciclos.saves == 1


async def test_update_empleado_valida_no_encontrado_y_email_duplicado() -> None:
    sector, cargo = _sector(), _cargo()
    uno = make_empleado(email="uno@canal.com", department_id=sector.id, cargo_id=cargo.id)
    dos = make_empleado(email="dos@canal.com", department_id=sector.id, cargo_id=cargo.id)
    deps = _deps(FakeEmpleadoRepo([uno, dos]), sector=sector, cargo=cargo)

    with pytest.raises(EmpleadoNoEncontradoError):
        await UpdateEmpleado(deps).execute(uuid.uuid4(), _command(sector, cargo))
    with pytest.raises(NombreDuplicadoError):
        await UpdateEmpleado(deps).execute(
            uno.id, _command(sector, cargo, email="dos@canal.com", hire_date=uno.hire_date)
        )


async def test_delete_empleado_y_no_encontrado() -> None:
    sector, cargo = _sector(), _cargo()
    empleado = make_empleado(department_id=sector.id, cargo_id=cargo.id)
    empleados = FakeEmpleadoRepo([empleado])
    deps = _deps(empleados, sector=sector, cargo=cargo)

    await DeleteEmpleado(deps).execute(empleado.id)
    assert await empleados.get_by_id(empleado.id) is None
    with pytest.raises(EmpleadoNoEncontradoError):
        await DeleteEmpleado(deps).execute(empleado.id)
