"""Ciclo de vida de solicitudes con repos fake: paridades del legacy."""

import uuid
from dataclasses import replace
from datetime import date

import pytest

from src.modules.vacaciones.application.dtos.solicitud_dtos import (
    CrearSolicitudCommand,
    DecidirSolicitudCommand,
    EditarSolicitudCommand,
)
from src.modules.vacaciones.application.use_cases.decidir_solicitud import (
    DecidirSolicitud,
    DecidirSolicitudDependencies,
)
from src.modules.vacaciones.application.use_cases.gestionar_solicitudes import (
    CrearSolicitud,
    EditarSolicitud,
    EliminarSolicitud,
    SolicitudesDependencies,
)
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_CREATE,
    ACCION_DELETE,
    ACCION_UPDATE,
    ENTIDAD_SOLICITUD,
)
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    AnioMuyLejanoError,
    EmpleadoNoEncontradoError,
    OperacionNoPermitidaError,
    SolicitudNoEncontradaError,
    SoloPendientesEditablesError,
)
from src.shared.domain.errors import ValidationError
from tests.unit.application.vacaciones.fakes import (
    FakeAprobacionRepo,
    FakeCargoRepo,
    FakeCicloRepo,
    FakeConfigRepo,
    FakeEmpleadoRepo,
    FakeExclusionRepo,
    FakeFeriadoRepo,
    FakeImpactoTurnosLookup,
    FakeNotificador,
    FakeRegistradorAuditoria,
    FakeSectorRepo,
    FakeSolicitudRepo,
    FixedClock,
)
from tests.unit.domain.vacaciones.factories import (
    make_actor,
    make_config,
    make_empleado,
    make_solicitud,
)

HOY = date(2026, 8, 13)


class _Escenario:
    def __init__(self) -> None:
        self.sector = Sector(
            id=uuid.uuid4(), name="Soporte", color="#2563eb", is_active=True
        )
        self.cargo = Cargo(id=uuid.uuid4(), name="Analista", max_simultaneos=None)
        self.empleado = make_empleado(
            hire_date=date(2019, 3, 15),
            department_id=self.sector.id,
            cargo_id=self.cargo.id,
        )
        self.solicitudes = FakeSolicitudRepo()
        self.ciclos = FakeCicloRepo()
        self.notificador = FakeNotificador()
        self.deps = SolicitudesDependencies(
            solicitudes=self.solicitudes,
            empleados=FakeEmpleadoRepo([self.empleado]),
            sectores=FakeSectorRepo([self.sector]),
            cargos=FakeCargoRepo([self.cargo]),
            ciclos=self.ciclos,
            exclusiones=FakeExclusionRepo(),
            feriados=FakeFeriadoRepo(),
            config=FakeConfigRepo(make_config()),
            clock=FixedClock(HOY),
            notificador=self.notificador,
        )


class TestCrearSolicitud:
    @pytest.mark.asyncio
    async def test_crea_pendiente_con_anio_imputado_y_notifica(self) -> None:
        esc = _Escenario()
        actor = make_actor(empleado_id=esc.empleado.id)
        command = CrearSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 11)
        )
        solicitud = await CrearSolicitud(esc.deps).execute(command, actor)

        assert solicitud.status is EstadoSolicitud.PENDING
        assert solicitud.charged_to_year == 2026
        assert solicitud.days_requested == 7  # fin viernes → +2 LCT
        assert len(esc.notificador.nuevas) == 1
        assert esc.notificador.nuevas[0].sector_nombre == "Soporte"

    @pytest.mark.asyncio
    async def test_crear_registra_auditoria_con_metadata(self) -> None:
        esc = _Escenario()
        auditoria = FakeRegistradorAuditoria()
        deps = replace(esc.deps, auditoria=auditoria)
        actor = make_actor(empleado_id=esc.empleado.id)
        command = CrearSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 11)
        )
        solicitud = await CrearSolicitud(deps).execute(command, actor)

        assert auditoria.registros == [
            (
                ACCION_CREATE,
                ENTIDAD_SOLICITUD,
                str(solicitud.id),
                {
                    "employee": esc.empleado.nombre_completo,
                    "startDate": "2026-09-07",
                    "endDate": "2026-09-11",
                    "days": 7,
                },
            )
        ]

    @pytest.mark.asyncio
    async def test_no_admin_ignora_empleado_id_ajeno(self) -> None:
        esc = _Escenario()
        actor = make_actor(empleado_id=esc.empleado.id)
        command = CrearSolicitudCommand(
            start_date=date(2026, 9, 7),
            end_date=date(2026, 9, 11),
            empleado_id=uuid.uuid4(),  # ignorado: no es admin
        )
        solicitud = await CrearSolicitud(esc.deps).execute(command, actor)
        assert solicitud.empleado_id == esc.empleado.id

    @pytest.mark.asyncio
    async def test_sin_empleado_vinculado_falla(self) -> None:
        esc = _Escenario()
        command = CrearSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 11)
        )
        with pytest.raises(ValidationError):
            await CrearSolicitud(esc.deps).execute(command, make_actor())

    @pytest.mark.asyncio
    async def test_anio_invalido_no_crea_ciclos(self) -> None:
        esc = _Escenario()
        actor = make_actor(empleado_id=esc.empleado.id)
        command = CrearSolicitudCommand(
            start_date=date(2028, 1, 5),
            end_date=date(2028, 1, 9),
            charged_to_year=2028,
        )
        with pytest.raises(AnioMuyLejanoError):
            await CrearSolicitud(esc.deps).execute(command, actor)
        assert esc.ciclos.items == {}  # el pre-chequeo evitó el ensure


class TestEditarSolicitud:
    @pytest.mark.asyncio
    async def test_editar_con_add_back_y_vuelve_a_pendiente(self) -> None:
        esc = _Escenario()
        existente = make_solicitud(
            empleado_id=esc.empleado.id,
            start_date=date(2026, 9, 7),
            end_date=date(2026, 9, 24),
            days_requested=20,
            status=EstadoSolicitud.APPROVED,
        )
        esc.solicitudes.items[existente.id] = existente
        actor = make_actor(es_admin=True)
        command = EditarSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 10)
        )
        # saldo: annual 21 - 20 usados = 1; add-back 20 → 21 disponibles para 4 días
        editada = await EditarSolicitud(esc.deps).execute(existente.id, command, actor)
        assert editada.days_requested == 4
        assert editada.status is EstadoSolicitud.PENDING

    @pytest.mark.asyncio
    async def test_editar_aplica_campos_y_audita_rango_previo(self) -> None:
        esc = _Escenario()
        auditoria = FakeRegistradorAuditoria()
        deps = replace(esc.deps, auditoria=auditoria)
        existente = make_solicitud(
            empleado_id=esc.empleado.id,
            start_date=date(2026, 9, 7),
            end_date=date(2026, 9, 10),
            days_requested=4,
        )
        esc.solicitudes.items[existente.id] = existente
        command = EditarSolicitudCommand(
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 8),
            charged_to_year=2026,
            reason="Viaje",
        )
        editada = await EditarSolicitud(deps).execute(
            existente.id, command, make_actor(empleado_id=esc.empleado.id)
        )

        assert (editada.start_date, editada.end_date) == (date(2026, 10, 5), date(2026, 10, 8))
        assert (editada.charged_to_year, editada.reason) == (2026, "Viaje")
        assert esc.solicitudes.items[existente.id] is editada
        assert auditoria.registros == [
            (
                ACCION_UPDATE,
                ENTIDAD_SOLICITUD,
                str(existente.id),
                {
                    "employee": esc.empleado.nombre_completo,
                    "startDate": "2026-10-05",
                    "endDate": "2026-10-08",
                    "days": 4,
                    "previousStart": "2026-09-07",
                    "previousEnd": "2026-09-10",
                },
            )
        ]

    @pytest.mark.asyncio
    async def test_editar_inexistente_falla(self) -> None:
        esc = _Escenario()
        command = EditarSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 10)
        )
        with pytest.raises(SolicitudNoEncontradaError):
            await EditarSolicitud(esc.deps).execute(
                uuid.uuid4(), command, make_actor(es_admin=True)
            )

    @pytest.mark.asyncio
    async def test_editar_sin_empleado_falla(self) -> None:
        esc = _Escenario()
        huerfana = make_solicitud(empleado_id=uuid.uuid4())
        esc.solicitudes.items[huerfana.id] = huerfana
        command = EditarSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 10)
        )
        with pytest.raises(EmpleadoNoEncontradoError):
            await EditarSolicitud(esc.deps).execute(
                huerfana.id, command, make_actor(es_admin=True)
            )

    @pytest.mark.asyncio
    async def test_tercero_no_puede_editar(self) -> None:
        esc = _Escenario()
        existente = make_solicitud(empleado_id=esc.empleado.id)
        esc.solicitudes.items[existente.id] = existente
        otro = make_actor(empleado_id=uuid.uuid4())
        command = EditarSolicitudCommand(
            start_date=date(2026, 9, 7), end_date=date(2026, 9, 10)
        )
        with pytest.raises(OperacionNoPermitidaError):
            await EditarSolicitud(esc.deps).execute(existente.id, command, otro)


class TestEliminarSolicitud:
    @pytest.mark.asyncio
    async def test_no_pendiente_bloqueada_sin_admin(self) -> None:
        esc = _Escenario()
        aprobada = make_solicitud(
            empleado_id=esc.empleado.id, status=EstadoSolicitud.APPROVED
        )
        esc.solicitudes.items[aprobada.id] = aprobada
        actor = make_actor(empleado_id=esc.empleado.id)
        with pytest.raises(SoloPendientesEditablesError):
            await EliminarSolicitud(esc.deps).execute(aprobada.id, actor)
        # admin sí puede
        await EliminarSolicitud(esc.deps).execute(aprobada.id, make_actor(es_admin=True))
        assert aprobada.id not in esc.solicitudes.items

    @pytest.mark.asyncio
    async def test_eliminar_inexistente_falla(self) -> None:
        esc = _Escenario()
        with pytest.raises(SolicitudNoEncontradaError):
            await EliminarSolicitud(esc.deps).execute(uuid.uuid4(), make_actor(es_admin=True))

    @pytest.mark.asyncio
    async def test_eliminar_registra_auditoria(self) -> None:
        esc = _Escenario()
        auditoria = FakeRegistradorAuditoria()
        deps = replace(esc.deps, auditoria=auditoria)
        pendiente = make_solicitud(empleado_id=esc.empleado.id)
        esc.solicitudes.items[pendiente.id] = pendiente
        await EliminarSolicitud(deps).execute(
            pendiente.id, make_actor(empleado_id=esc.empleado.id)
        )
        assert auditoria.registros == [
            (
                ACCION_DELETE,
                ENTIDAD_SOLICITUD,
                str(pendiente.id),
                {
                    "employee": esc.empleado.nombre_completo,
                    "startDate": "2026-08-03",
                    "endDate": "2026-08-13",
                    "days": 10,
                },
            )
        ]


class TestDecidirSolicitud:
    def _deps(self, esc: _Escenario) -> DecidirSolicitudDependencies:
        return DecidirSolicitudDependencies(
            solicitudes=esc.solicitudes,
            empleados=FakeEmpleadoRepo([esc.empleado]),
            aprobaciones=self.aprobaciones,
            notificador=esc.notificador,
        )

    @pytest.mark.asyncio
    async def test_jefe_decide_con_historial_y_notificacion(self) -> None:
        esc = _Escenario()
        self.aprobaciones = FakeAprobacionRepo()
        pendiente = make_solicitud(empleado_id=esc.empleado.id)
        esc.solicitudes.items[pendiente.id] = pendiente
        jefe = make_actor(sector_gestionado_id=esc.sector.id)

        decidida = await DecidirSolicitud(self._deps(esc)).execute(
            pendiente.id, DecidirSolicitudCommand(decision="APPROVED", comment="OK"), jefe
        )

        assert decidida.solicitud.status is EstadoSolicitud.APPROVED
        assert decidida.afecta_turnos is None  # empleado sin cuenta vinculada
        assert len(self.aprobaciones.items) == 1
        assert self.aprobaciones.items[0].comment == "OK"
        assert len(esc.notificador.decisiones) == 1
        assert esc.notificador.decisiones[0].aprobada is True

    @pytest.mark.asyncio
    async def test_re_decidir_esta_permitido(self) -> None:
        esc = _Escenario()
        self.aprobaciones = FakeAprobacionRepo()
        aprobada = make_solicitud(
            empleado_id=esc.empleado.id, status=EstadoSolicitud.APPROVED
        )
        esc.solicitudes.items[aprobada.id] = aprobada

        decidida = await DecidirSolicitud(self._deps(esc)).execute(
            aprobada.id,
            DecidirSolicitudCommand(decision="REJECTED", comment=None),
            make_actor(es_admin=True),
        )
        assert decidida.solicitud.status is EstadoSolicitud.REJECTED
        assert len(self.aprobaciones.items) == 1  # historial acumula

    @pytest.mark.asyncio
    async def test_jefe_de_otro_sector_no_decide(self) -> None:
        esc = _Escenario()
        self.aprobaciones = FakeAprobacionRepo()
        pendiente = make_solicitud(empleado_id=esc.empleado.id)
        esc.solicitudes.items[pendiente.id] = pendiente
        ajeno = make_actor(sector_gestionado_id=uuid.uuid4())
        with pytest.raises(OperacionNoPermitidaError):
            await DecidirSolicitud(self._deps(esc)).execute(
                pendiente.id, DecidirSolicitudCommand(decision="APPROVED"), ajeno
            )

    @pytest.mark.asyncio
    async def test_aprobar_avisa_afecta_turnos_si_el_empleado_vinculado_tiene_franjas(
        self,
    ) -> None:
        """ADR-025: el aviso alimenta el CTA de Aprobaciones; no crea la grilla."""
        esc = _Escenario()
        self.aprobaciones = FakeAprobacionRepo()
        user_id = uuid.uuid4()
        esc.empleado.user_id = user_id
        pendiente = make_solicitud(
            empleado_id=esc.empleado.id, start_date=date(2026, 8, 24), end_date=date(2026, 8, 28)
        )
        esc.solicitudes.items[pendiente.id] = pendiente
        lookup = FakeImpactoTurnosLookup({user_id})
        deps = DecidirSolicitudDependencies(
            solicitudes=esc.solicitudes,
            empleados=FakeEmpleadoRepo([esc.empleado]),
            aprobaciones=self.aprobaciones,
            notificador=esc.notificador,
            impacto_turnos=lookup,
        )

        aprobada = await DecidirSolicitud(deps).execute(
            pendiente.id, DecidirSolicitudCommand(decision="APPROVED"), make_actor(es_admin=True)
        )

        assert aprobada.afecta_turnos is not None
        assert (aprobada.afecta_turnos.user_id, aprobada.afecta_turnos.desde) == (
            user_id,
            date(2026, 8, 24),
        )
        assert lookup.consultas == [(user_id, date(2026, 8, 24), date(2026, 8, 28))]

    @pytest.mark.asyncio
    async def test_rechazar_no_consulta_turnos_ni_avisa(self) -> None:
        esc = _Escenario()
        self.aprobaciones = FakeAprobacionRepo()
        esc.empleado.user_id = uuid.uuid4()
        pendiente = make_solicitud(empleado_id=esc.empleado.id)
        esc.solicitudes.items[pendiente.id] = pendiente
        lookup = FakeImpactoTurnosLookup({esc.empleado.user_id})
        deps = DecidirSolicitudDependencies(
            solicitudes=esc.solicitudes,
            empleados=FakeEmpleadoRepo([esc.empleado]),
            aprobaciones=self.aprobaciones,
            notificador=esc.notificador,
            impacto_turnos=lookup,
        )

        rechazada = await DecidirSolicitud(deps).execute(
            pendiente.id, DecidirSolicitudCommand(decision="REJECTED"), make_actor(es_admin=True)
        )

        assert rechazada.afecta_turnos is None
        assert lookup.consultas == []
