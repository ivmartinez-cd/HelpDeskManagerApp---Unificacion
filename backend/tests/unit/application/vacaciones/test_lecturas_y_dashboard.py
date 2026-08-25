"""Lecturas enriquecidas (solicitudes, ausencias), calendario, dashboard y
reporte de descuentos."""

import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.vacaciones.application.dtos.ausencia_dtos import ListarAusenciasQuery
from src.modules.vacaciones.application.dtos.solicitud_dtos import ListarSolicitudesQuery
from src.modules.vacaciones.application.use_cases.calendario_eventos import (
    CalendarioDependencies,
    CalendarioEventos,
)
from src.modules.vacaciones.application.use_cases.dashboard_resumen import (
    DashboardDependencies,
    DashboardResumen,
)
from src.modules.vacaciones.application.use_cases.leer_ausencias import (
    LeerAusenciasDependencies,
    ListarAusencias,
)
from src.modules.vacaciones.application.use_cases.leer_solicitudes import (
    LeerSolicitudesDependencies,
    ListarSolicitudes,
    ObtenerSolicitud,
)
from src.modules.vacaciones.application.use_cases.reporte_descuentos import (
    ReporteDescuentos,
    ReporteDescuentosDependencies,
)
from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion, Decision
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    OperacionNoPermitidaError,
    SolicitudNoEncontradaError,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserInfo
from tests.unit.application.vacaciones.fakes import (
    FakeAprobacionRepo,
    FakeAusenciaRepo,
    FakeCargoRepo,
    FakeCicloRepo,
    FakeConfigRepo,
    FakeEmpleadoRepo,
    FakeFeriadoRepo,
    FakeSectorRepo,
    FakeSolicitudRepo,
    FakeUserDirectory,
    FixedClock,
)
from tests.unit.domain.vacaciones.factories import (
    make_actor,
    make_config,
    make_empleado,
    make_solicitud,
)

_HOY = date(2026, 8, 14)


def _sector() -> Sector:
    return Sector(id=uuid.uuid4(), name="Mesa", color="#123", is_active=True)


def _ausencia(empleado_id: uuid.UUID, **overrides: object) -> Ausencia:
    base: dict[str, object] = {
        "id": uuid.uuid4(),
        "empleado_id": empleado_id,
        "start_date": date(2026, 8, 10),
        "end_date": date(2026, 8, 11),
        "days_count": 2,
        "half_day": False,
        "tipo": TipoAusencia.BAJA_ENFERMEDAD,
        "reason": None,
        "status": EstadoSolicitud.APPROVED,
        "created_at": datetime(2026, 8, 1, tzinfo=UTC),
    }
    base.update(overrides)
    return Ausencia(**base)  # type: ignore[arg-type]


def _ciclo(empleado_id: uuid.UUID, year: int = 2026) -> Ciclo:
    return Ciclo(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        year=year,
        annual_days=14,
        carry_over=0,
        is_open=True,
        opened_at=datetime.now(UTC),
    )


# ------------------------------------------------------------------ ausencias


async def test_listar_ausencias_enriquece_y_scopea() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    deps = LeerAusenciasDependencies(
        ausencias=FakeAusenciaRepo([_ausencia(empleado.id)]),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([sector]),
    )

    dtos = await ListarAusencias(deps).execute(ListarAusenciasQuery(), make_actor(es_admin=True))
    assert len(dtos) == 1
    assert dtos[0].empleado_nombre == empleado.nombre_completo
    assert dtos[0].sector_nombre == "Mesa"

    assert await ListarAusencias(deps).execute(ListarAusenciasQuery(), make_actor()) == []


# ---------------------------------------------------------------- solicitudes


async def test_listar_solicitudes_enriquece_con_aprobaciones() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    solicitud = make_solicitud(empleado_id=empleado.id)
    approver = UserInfo(id=uuid.uuid4(), email="jefa@cd.com", full_name="Jefa")
    aprobaciones = FakeAprobacionRepo()
    aprobaciones.items.append(
        Aprobacion(
            id=uuid.uuid4(),
            solicitud_id=solicitud.id,
            approver_user_id=approver.id,
            decision=Decision.APPROVED,
            comment=None,
            created_at=datetime(2026, 8, 2, tzinfo=UTC),
        )
    )
    deps = LeerSolicitudesDependencies(
        solicitudes=FakeSolicitudRepo([solicitud]),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([sector]),
        aprobaciones=aprobaciones,
        users=FakeUserDirectory([approver]),
    )

    dtos = await ListarSolicitudes(deps).execute(
        ListarSolicitudesQuery(), make_actor(es_admin=True)
    )

    assert len(dtos) == 1
    assert dtos[0].empleado_nombre == empleado.nombre_completo
    assert dtos[0].aprobaciones[0].approver_email == "jefa@cd.com"

    assert (
        await ListarSolicitudes(deps).execute(ListarSolicitudesQuery(), make_actor()) == []
    )


async def test_listar_solicitudes_por_fecha_incluye_las_que_ya_empezaron() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    en_curso = make_solicitud(
        empleado_id=empleado.id,
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 28),
        status=EstadoSolicitud.APPROVED,
    )
    deps = LeerSolicitudesDependencies(
        solicitudes=FakeSolicitudRepo([en_curso]),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([sector]),
        aprobaciones=FakeAprobacionRepo(),
        users=FakeUserDirectory(),
    )

    dtos = await ListarSolicitudes(deps).execute(
        ListarSolicitudesQuery(desde=date(2026, 8, 25), hasta=date(2026, 9, 15)),
        make_actor(es_admin=True),
    )
    assert len(dtos) == 1

    dtos_luego_de_terminar = await ListarSolicitudes(deps).execute(
        ListarSolicitudesQuery(desde=date(2026, 8, 29), hasta=date(2026, 9, 15)),
        make_actor(es_admin=True),
    )
    assert dtos_luego_de_terminar == []


async def test_obtener_solicitud_controla_acceso_y_no_encontrada() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    solicitud = make_solicitud(empleado_id=empleado.id)
    deps = LeerSolicitudesDependencies(
        solicitudes=FakeSolicitudRepo([solicitud]),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([sector]),
        aprobaciones=FakeAprobacionRepo(),
        users=FakeUserDirectory(),
    )

    dto = await ObtenerSolicitud(deps).execute(
        solicitud.id, make_actor(empleado_id=empleado.id)
    )
    assert dto.solicitud is solicitud

    with pytest.raises(OperacionNoPermitidaError):
        await ObtenerSolicitud(deps).execute(
            solicitud.id, make_actor(empleado_id=uuid.uuid4())
        )
    with pytest.raises(SolicitudNoEncontradaError):
        await ObtenerSolicitud(deps).execute(uuid.uuid4(), make_actor(es_admin=True))


# ----------------------------------------------------------------- calendario


async def test_calendario_mezcla_vacaciones_con_restante_y_feriados() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    primera = make_solicitud(
        empleado_id=empleado.id,
        start_date=date(2026, 8, 3),
        end_date=date(2026, 8, 7),
        days_requested=5,
        status=EstadoSolicitud.APPROVED,
    )
    segunda = make_solicitud(
        empleado_id=empleado.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 5),
        days_requested=5,
    )
    feriado = Feriado(
        id=uuid.uuid4(), name="Feriado X", date=date(2026, 8, 17), deducts_vacation=False
    )
    deps = CalendarioDependencies(
        solicitudes=FakeSolicitudRepo([primera, segunda]),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([sector]),
        feriados=FakeFeriadoRepo([feriado]),
        ciclos=FakeCicloRepo([_ciclo(empleado.id)]),
        config=FakeConfigRepo(make_config()),
        clock=FixedClock(_HOY),
    )

    eventos = await CalendarioEventos(deps).execute(None, None, make_actor(es_admin=True))

    vacaciones = [e for e in eventos if e.tipo == "vacation"]
    feriados = [e for e in eventos if e.tipo == "holiday"]
    assert len(vacaciones) == 2 and len(feriados) == 1
    # annual 14 (+0 carry): tras la primera de 5 quedan 9; tras la segunda, 4.
    por_inicio = sorted(vacaciones, key=lambda e: e.start)
    assert por_inicio[0].restantes == 9
    assert por_inicio[1].restantes == 4
    assert feriados[0].titulo == "Feriado X"


# ------------------------------------------------------------------ dashboard


async def test_dashboard_admin_suma_saldos_del_equipo() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    en_vacaciones = make_solicitud(
        empleado_id=empleado.id,
        start_date=date(2026, 8, 10),
        end_date=date(2026, 8, 20),
        days_requested=9,
        status=EstadoSolicitud.APPROVED,
    )
    pendiente = make_solicitud(empleado_id=empleado.id, start_date=date(2026, 9, 1))
    deps = DashboardDependencies(
        empleados=FakeEmpleadoRepo([empleado]),
        solicitudes=FakeSolicitudRepo([en_vacaciones, pendiente]),
        sectores=FakeSectorRepo([sector]),
        ciclos=FakeCicloRepo([_ciclo(empleado.id)]),
        config=FakeConfigRepo(make_config()),
        clock=FixedClock(_HOY),
    )

    resumen = await DashboardResumen(deps).execute(make_actor(es_admin=True))

    assert resumen.total_empleados == 1 and resumen.empleados_activos == 1
    assert resumen.solicitudes_pendientes == 1
    assert [v.empleado_nombre for v in resumen.en_vacaciones] == [empleado.nombre_completo]
    assert resumen.dias is None  # admin sin empleado vinculado
    assert resumen.dias_totales_equipo == 14


async def test_dashboard_empleado_ve_su_saldo() -> None:
    sector = _sector()
    empleado = make_empleado(department_id=sector.id)
    deps = DashboardDependencies(
        empleados=FakeEmpleadoRepo([empleado]),
        solicitudes=FakeSolicitudRepo(),
        sectores=FakeSectorRepo([sector]),
        ciclos=FakeCicloRepo([_ciclo(empleado.id)]),
        config=FakeConfigRepo(make_config()),
        clock=FixedClock(_HOY),
    )

    resumen = await DashboardResumen(deps).execute(make_actor(empleado_id=empleado.id))

    assert resumen.dias is not None and resumen.dias.saldo.annual == 14
    assert resumen.dias_totales_equipo is None  # solo admin ve los del equipo


# ------------------------------------------------------------------- reporte


async def test_reporte_descuentos_usa_el_sector_tecnico_por_defecto() -> None:
    tecnico = Sector(id=uuid.uuid4(), name="Técnico", color="#123", is_active=True)
    cargo = Cargo(id=uuid.uuid4(), name="Técnico de campo", max_simultaneos=None)
    empleado = make_empleado(department_id=tecnico.id, cargo_id=cargo.id)
    ausencia = _ausencia(
        empleado.id,
        tipo=TipoAusencia.GUARDIA,
        start_date=date(2026, 8, 10),
        end_date=date(2026, 8, 11),
    )
    deps = ReporteDescuentosDependencies(
        ausencias=FakeAusenciaRepo([ausencia]),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([tecnico, _sector()]),
        cargos=FakeCargoRepo([cargo]),
        feriados=FakeFeriadoRepo(),
    )

    filas = await ReporteDescuentos(deps).execute(2026, 8, None, make_actor(es_admin=True))

    assert len(filas) == 1
    assert filas[0].cargo_nombre == "Técnico de campo"
    assert filas[0].guardias == 2.0


async def test_reporte_descuentos_jefe_queda_clavado_a_su_sector() -> None:
    mesa = _sector()
    otro = Sector(id=uuid.uuid4(), name="Otro", color="#123", is_active=True)
    empleado = make_empleado(department_id=mesa.id)
    deps = ReporteDescuentosDependencies(
        ausencias=FakeAusenciaRepo(),
        empleados=FakeEmpleadoRepo([empleado]),
        sectores=FakeSectorRepo([mesa, otro]),
        cargos=FakeCargoRepo([]),
        feriados=FakeFeriadoRepo(),
    )

    jefe = make_actor(sector_gestionado_id=mesa.id)
    filas = await ReporteDescuentos(deps).execute(2026, 8, otro.id, jefe)
    assert len(filas) == 1  # ignoró el department_id pedido, usó el suyo

    sin_sector = await ReporteDescuentos(deps).execute(2026, 8, None, make_actor(es_admin=True))
    assert sin_sector == []  # sin sector "Técnico" y sin department_id: vacío
