"""ReporteVacaciones: paridad con buildEmployeeReport/buildDepartmentReport
del legacy — incluye inactivos, ordena empleados por nombre y sectores por
nombre, y agrega los saldos del año en curso."""

import uuid
from datetime import date

import pytest

from src.modules.vacaciones.application.use_cases.reporte_vacaciones import (
    ReporteVacaciones,
    ReporteVacacionesDependencies,
)
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from tests.unit.application.vacaciones.fakes import (
    FakeCargoRepo,
    FakeCicloRepo,
    FakeConfigRepo,
    FakeEmpleadoRepo,
    FakeSectorRepo,
    FakeSolicitudRepo,
    FixedClock,
)
from tests.unit.domain.vacaciones.factories import (
    make_config,
    make_empleado,
    make_solicitud,
)

HOY = date(2026, 8, 13)


class Harness:
    def __init__(self) -> None:
        self.sector_a = Sector(
            id=uuid.uuid4(), name="Administración", color="#d97706", is_active=True
        )
        self.sector_b = Sector(
            id=uuid.uuid4(), name="Soporte Técnico", color="#2563eb", is_active=True
        )
        self.cargo = Cargo(id=uuid.uuid4(), name="Técnico", max_simultaneos=None)
        # Contratados en 2019 → a la referencia 2026-01-01 caen en el tier de 21 días.
        self.ana = make_empleado(
            first_name="Ana",
            last_name="Martínez",
            department_id=self.sector_a.id,
            cargo_id=self.cargo.id,
        )
        self.bruno = make_empleado(
            first_name="Bruno",
            last_name="Suárez",
            department_id=self.sector_a.id,
            cargo_id=self.cargo.id,
            status=EstadoEmpleado.INACTIVE,
        )
        self.carla = make_empleado(
            first_name="Carla",
            last_name="Rodríguez",
            department_id=self.sector_b.id,
            cargo_id=self.cargo.id,
        )
        self.solicitudes = FakeSolicitudRepo(
            [
                make_solicitud(
                    empleado_id=self.ana.id,
                    days_requested=10,
                    status=EstadoSolicitud.APPROVED,
                ),
                make_solicitud(
                    empleado_id=self.carla.id,
                    days_requested=5,
                    status=EstadoSolicitud.PENDING,
                ),
            ]
        )
        self.deps = ReporteVacacionesDependencies(
            empleados=FakeEmpleadoRepo([self.carla, self.bruno, self.ana]),
            sectores=FakeSectorRepo([self.sector_b, self.sector_a]),
            cargos=FakeCargoRepo([self.cargo]),
            ciclos=FakeCicloRepo(),
            solicitudes=self.solicitudes,
            config=FakeConfigRepo(make_config()),
            clock=FixedClock(HOY),
        )


@pytest.mark.asyncio
async def test_por_empleado_ordena_por_nombre_e_incluye_inactivos() -> None:
    h = Harness()
    reporte = await ReporteVacaciones(h.deps).execute()
    assert reporte.year == 2026
    assert [f.nombre for f in reporte.por_empleado] == [
        "Ana Martínez",
        "Bruno Suárez",
        "Carla Rodríguez",
    ]
    ana = reporte.por_empleado[0]
    assert (ana.sector_nombre, ana.cargo_nombre) == ("Administración", "Técnico")
    assert (ana.annual, ana.used, ana.pending, ana.available) == (21, 10, 0, 11)
    carla = reporte.por_empleado[2]
    assert (carla.annual, carla.used, carla.pending, carla.available) == (21, 0, 5, 16)


@pytest.mark.asyncio
async def test_por_sector_agrega_saldos_y_ordena_por_nombre() -> None:
    h = Harness()
    reporte = await ReporteVacaciones(h.deps).execute()
    assert [f.nombre for f in reporte.por_sector] == ["Administración", "Soporte Técnico"]
    admin = reporte.por_sector[0]
    assert admin.color == "#d97706"
    # Ana (21/10/11) + Bruno inactivo (21/0/21): el legacy también lo cuenta.
    assert (admin.empleados, admin.annual, admin.used, admin.available) == (2, 42, 10, 32)
    soporte = reporte.por_sector[1]
    assert (soporte.empleados, soporte.annual, soporte.used, soporte.available) == (
        1,
        21,
        0,
        16,
    )
