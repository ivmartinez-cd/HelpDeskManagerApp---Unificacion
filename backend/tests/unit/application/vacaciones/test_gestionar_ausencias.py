"""Ciclo de vida de bajas: alta (propia y masiva), solapes, edición y borrado
con las reglas exactas del absence.controller legacy, más la auditoría."""

import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.vacaciones.application.dtos.ausencia_dtos import (
    CrearAusenciaCommand,
    EditarAusenciaCommand,
)
from src.modules.vacaciones.application.use_cases.gestionar_ausencias import (
    AusenciasDependencies,
    CrearAusencias,
    EditarAusencia,
    EliminarAusencia,
)
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import (
    OperacionNoPermitidaError,
    SolapamientoAusenciaError,
    SolapamientoConVacacionesError,
)
from tests.unit.application.vacaciones.fakes import (
    FakeAusenciaRepo,
    FakeEmpleadoRepo,
    FakeRegistradorAuditoria,
    FakeSolicitudRepo,
)
from tests.unit.domain.vacaciones.factories import (
    make_actor,
    make_empleado,
    make_solicitud,
)


def _ausencia(empleado_id: uuid.UUID, **overrides: object) -> Ausencia:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "empleado_id": empleado_id,
        "start_date": date(2026, 8, 3),
        "end_date": date(2026, 8, 4),
        "days_count": 2,
        "half_day": False,
        "tipo": TipoAusencia.BAJA_ENFERMEDAD,
        "reason": None,
        "status": EstadoSolicitud.APPROVED,
        "created_at": datetime(2026, 8, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Ausencia(**defaults)  # type: ignore[arg-type]


def _deps(
    empleados: list, ausencias: list | None = None, solicitudes: list | None = None
) -> tuple[AusenciasDependencies, FakeRegistradorAuditoria]:
    auditoria = FakeRegistradorAuditoria()
    deps = AusenciasDependencies(
        ausencias=FakeAusenciaRepo(ausencias),
        empleados=FakeEmpleadoRepo(empleados),
        solicitudes=FakeSolicitudRepo(solicitudes),
        auditoria=auditoria,
    )
    return deps, auditoria


def _command(**overrides: object) -> CrearAusenciaCommand:
    defaults: dict[str, object] = {
        "empleado_ids": [],
        "start_date": date(2026, 8, 3),
        "end_date": date(2026, 8, 4),
        "tipo": TipoAusencia.BAJA_ENFERMEDAD,
        "reason": None,
        "half_day": False,
    }
    defaults.update(overrides)
    return CrearAusenciaCommand(**defaults)  # type: ignore[arg-type]


class TestCrearAusencias:
    async def test_empleado_crea_la_propia_aprobada(self) -> None:
        empleado = make_empleado()
        deps, auditoria = _deps([empleado])
        actor = make_actor(empleado_id=empleado.id)
        creadas = await CrearAusencias(deps).execute(_command(), actor)
        assert len(creadas) == 1
        assert creadas[0].status is EstadoSolicitud.APPROVED
        assert creadas[0].days_count == 2
        assert auditoria.registros[0][0:2] == ("CREATE", "Absence")

    async def test_admin_alta_masiva(self) -> None:
        e1, e2 = make_empleado(), make_empleado()
        deps, auditoria = _deps([e1, e2])
        actor = make_actor(es_admin=True)
        creadas = await CrearAusencias(deps).execute(
            _command(empleado_ids=[e1.id, e2.id]), actor
        )
        assert {a.empleado_id for a in creadas} == {e1.id, e2.id}
        assert len(auditoria.registros) == 2

    async def test_solape_mismo_tipo_conflicto(self) -> None:
        empleado = make_empleado()
        existente = _ausencia(empleado.id)
        deps, _ = _deps([empleado], ausencias=[existente])
        actor = make_actor(empleado_id=empleado.id)
        with pytest.raises(SolapamientoAusenciaError):
            await CrearAusencias(deps).execute(_command(), actor)

    async def test_otro_tipo_no_conflictua(self) -> None:
        empleado = make_empleado()
        existente = _ausencia(empleado.id, tipo=TipoAusencia.HOME_OFFICE)
        deps, _ = _deps([empleado], ausencias=[existente])
        actor = make_actor(empleado_id=empleado.id)
        creadas = await CrearAusencias(deps).execute(_command(), actor)
        assert len(creadas) == 1

    async def test_solape_con_vacaciones_conflicto(self) -> None:
        empleado = make_empleado()
        solicitud = make_solicitud(
            empleado_id=empleado.id,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 10),
        )
        deps, _ = _deps([empleado], solicitudes=[solicitud])
        actor = make_actor(empleado_id=empleado.id)
        with pytest.raises(SolapamientoConVacacionesError):
            await CrearAusencias(deps).execute(_command(), actor)


class TestEditarAusencia:
    async def test_admin_edita_y_cambia_estado(self) -> None:
        empleado = make_empleado()
        ausencia = _ausencia(empleado.id)
        deps, auditoria = _deps([empleado], ausencias=[ausencia])
        command = EditarAusenciaCommand(
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 5),
            tipo=TipoAusencia.BAJA_ENFERMEDAD,
            reason="reposo",
            half_day=False,
            status=EstadoSolicitud.REJECTED,
        )
        editada = await EditarAusencia(deps).execute(
            ausencia.id, command, make_actor(es_admin=True)
        )
        assert editada.status is EstadoSolicitud.REJECTED
        assert editada.days_count == 3
        assert auditoria.registros[0][0:2] == ("UPDATE", "Absence")

    async def test_no_admin_no_cambia_estado(self) -> None:
        empleado = make_empleado()
        ausencia = _ausencia(empleado.id, status=EstadoSolicitud.PENDING)
        deps, _ = _deps([empleado], ausencias=[ausencia])
        command = EditarAusenciaCommand(
            start_date=ausencia.start_date,
            end_date=ausencia.end_date,
            tipo=ausencia.tipo,
            reason=None,
            half_day=False,
            status=EstadoSolicitud.APPROVED,
        )
        with pytest.raises(OperacionNoPermitidaError):
            await EditarAusencia(deps).execute(
                ausencia.id, command, make_actor(empleado_id=empleado.id)
            )

    async def test_re_valida_solape_solo_si_cambia_agenda(self) -> None:
        empleado = make_empleado()
        ausencia = _ausencia(empleado.id)
        otra = _ausencia(
            empleado.id, start_date=date(2026, 8, 10), end_date=date(2026, 8, 11)
        )
        deps, _ = _deps([empleado], ausencias=[ausencia, otra])
        command = EditarAusenciaCommand(
            start_date=date(2026, 8, 9),
            end_date=date(2026, 8, 10),
            tipo=ausencia.tipo,
            reason=None,
            half_day=False,
            status=None,
        )
        with pytest.raises(SolapamientoAusenciaError):
            await EditarAusencia(deps).execute(
                ausencia.id, command, make_actor(es_admin=True)
            )


class TestEliminarAusencia:
    async def test_dueno_solo_borra_pendientes(self) -> None:
        empleado = make_empleado()
        ausencia = _ausencia(empleado.id)  # APPROVED
        deps, _ = _deps([empleado], ausencias=[ausencia])
        with pytest.raises(Exception, match="pendientes"):
            await EliminarAusencia(deps).execute(
                ausencia.id, make_actor(empleado_id=empleado.id)
            )

    async def test_admin_borra_y_audita(self) -> None:
        empleado = make_empleado()
        ausencia = _ausencia(empleado.id)
        deps, auditoria = _deps([empleado], ausencias=[ausencia])
        await EliminarAusencia(deps).execute(ausencia.id, make_actor(es_admin=True))
        assert auditoria.registros[0][0:2] == ("DELETE", "Absence")
