"""SaldosService: ensure lazy de ciclos, write-behind del carry y upgrade de
apertura."""

import uuid
from datetime import date

import pytest

from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from tests.unit.application.vacaciones.fakes import (
    FakeCicloRepo,
    FakeConfigRepo,
    FakeEmpleadoRepo,
    FakeSolicitudRepo,
    FixedClock,
)
from tests.unit.domain.vacaciones.factories import make_config, make_empleado, make_solicitud

HOY = date(2026, 8, 13)


def _service(
    empleados: FakeEmpleadoRepo,
    ciclos: FakeCicloRepo,
    solicitudes: FakeSolicitudRepo,
    config=None,  # type: ignore[no-untyped-def]
) -> SaldosService:
    return SaldosService(
        SaldosDependencies(
            empleados=empleados,
            ciclos=ciclos,
            solicitudes=solicitudes,
            config=FakeConfigRepo(config or make_config()),
            clock=FixedClock(HOY),
        )
    )


@pytest.mark.asyncio
async def test_crea_ciclos_faltantes_con_annual_por_antiguedad() -> None:
    empleado = make_empleado(hire_date=date(2019, 3, 15))  # ~6.8 años al 1/1/2026
    ciclos = FakeCicloRepo()
    service = _service(FakeEmpleadoRepo([empleado]), ciclos, FakeSolicitudRepo())

    saldo = await service.saldo_de(empleado, 2026)

    assert saldo.annual == 21  # tier 5-10
    assert saldo.available == 21
    creado = await ciclos.get(empleado.id, 2026)
    assert creado is not None
    assert creado.is_open is True  # año actual siempre abierto


@pytest.mark.asyncio
async def test_write_behind_del_carry_over() -> None:
    empleado = make_empleado(hire_date=date(2019, 3, 15))
    ciclos = FakeCicloRepo()
    solicitudes = FakeSolicitudRepo(
        [
            make_solicitud(
                empleado_id=empleado.id,
                start_date=date(2026, 2, 2),
                end_date=date(2026, 2, 12),
                days_requested=11,
                charged_to_year=2026,
                status=EstadoSolicitud.APPROVED,
            )
        ]
    )
    service = _service(FakeEmpleadoRepo([empleado]), ciclos, solicitudes)

    saldo_2027 = await service.saldo_de(empleado, 2027)

    # 2026: 21 - 11 = 10 disponibles → carry 2027 = 10, persistido en el ciclo
    assert saldo_2027.carry_over == 10
    ciclo_2027 = await ciclos.get(empleado.id, 2027)
    assert ciclo_2027 is not None
    assert ciclo_2027.carry_over == 10


@pytest.mark.asyncio
async def test_upgrade_lazy_de_apertura() -> None:
    empleado = make_empleado()
    cerrado = Ciclo(
        id=uuid.uuid4(),
        empleado_id=empleado.id,
        year=2026,
        annual_days=21,
        carry_over=0,
        is_open=False,  # quedó cerrado pero la política dice abierto (año actual)
        opened_at=None,
    )
    ciclos = FakeCicloRepo([cerrado])
    service = _service(FakeEmpleadoRepo([empleado]), ciclos, FakeSolicitudRepo())

    saldo = await service.saldo_de(empleado, 2026)

    assert saldo.cycle_open is True
    assert cerrado.is_open is True
    assert cerrado.opened_at is not None
