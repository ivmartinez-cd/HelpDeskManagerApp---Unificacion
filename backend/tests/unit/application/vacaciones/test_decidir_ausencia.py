"""DecidirAusencia: aprobar/rechazar una baja PENDING pedida por un empleado
(home office, cambio de horario). Mismos alcances que las solicitudes y aviso
`afecta_turnos` si el empleado tiene franjas en el rango."""

import uuid
from datetime import UTC, date, datetime, time

import pytest

from src.modules.vacaciones.application.dtos.ausencia_dtos import DecidirAusenciaCommand
from src.modules.vacaciones.application.use_cases.decidir_ausencia import (
    DecidirAusencia,
    DecidirAusenciaDependencies,
)
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import OperacionNoPermitidaError
from tests.unit.application.vacaciones.fakes import (
    FakeAusenciaRepo,
    FakeEmpleadoRepo,
    FakeRegistradorAuditoria,
)
from tests.unit.domain.vacaciones.factories import make_actor, make_empleado


class _ImpactoSiempre:
    def __init__(self, afecta: bool) -> None:
        self._afecta = afecta
        self.consultas: list[tuple[uuid.UUID, date, date]] = []

    async def tiene_turnos_en(self, user_id: uuid.UUID, desde: date, hasta: date) -> bool:
        self.consultas.append((user_id, desde, hasta))
        return self._afecta


def _pendiente(empleado_id: uuid.UUID) -> Ausencia:
    return Ausencia(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        start_date=date(2026, 8, 24),
        end_date=date(2026, 8, 28),
        days_count=5,
        half_day=False,
        tipo=TipoAusencia.CAMBIO_HORARIO,
        reason="Semana con horario corrido",
        status=EstadoSolicitud.PENDING,
        created_at=datetime.now(UTC),
        hora_desde=time(8, 0),
        hora_hasta=time(17, 0),
    )


def _deps(
    empleado, ausencia: Ausencia, afecta: bool = False
) -> tuple[DecidirAusenciaDependencies, FakeRegistradorAuditoria, _ImpactoSiempre]:
    auditoria = FakeRegistradorAuditoria()
    impacto = _ImpactoSiempre(afecta)
    deps = DecidirAusenciaDependencies(
        ausencias=FakeAusenciaRepo([ausencia]),
        empleados=FakeEmpleadoRepo([empleado]),
        auditoria=auditoria,
        impacto_turnos=impacto,
    )
    return deps, auditoria, impacto


async def test_admin_aprueba_y_avisa_impacto_en_turnos() -> None:
    empleado = make_empleado(user_id=uuid.uuid4())
    ausencia = _pendiente(empleado.id)
    deps, auditoria, impacto = _deps(empleado, ausencia, afecta=True)

    resultado = await DecidirAusencia(deps).execute(
        ausencia.id,
        DecidirAusenciaCommand(decision="APPROVED", comment="ok"),
        make_actor(es_admin=True),
    )

    assert resultado.ausencia.status is EstadoSolicitud.APPROVED
    assert resultado.afecta_turnos is not None
    assert (resultado.afecta_turnos.desde, resultado.afecta_turnos.hasta) == (
        date(2026, 8, 24),
        date(2026, 8, 28),
    )
    assert impacto.consultas == [(empleado.user_id, date(2026, 8, 24), date(2026, 8, 28))]
    assert auditoria.registros[0][0:2] == ("APPROVE", "Absence")
    assert auditoria.registros[0][3]["schedule"] == "08:00–17:00"


async def test_rechazo_no_consulta_turnos() -> None:
    empleado = make_empleado(user_id=uuid.uuid4())
    ausencia = _pendiente(empleado.id)
    deps, auditoria, impacto = _deps(empleado, ausencia, afecta=True)

    resultado = await DecidirAusencia(deps).execute(
        ausencia.id, DecidirAusenciaCommand(decision="REJECTED"), make_actor(es_admin=True)
    )

    assert resultado.ausencia.status is EstadoSolicitud.REJECTED
    assert resultado.afecta_turnos is None
    assert impacto.consultas == []
    assert auditoria.registros[0][0] == "REJECT"


async def test_sin_cuenta_vinculada_no_hay_aviso_de_turnos() -> None:
    empleado = make_empleado(user_id=None)
    ausencia = _pendiente(empleado.id)
    deps, _, impacto = _deps(empleado, ausencia, afecta=True)

    resultado = await DecidirAusencia(deps).execute(
        ausencia.id, DecidirAusenciaCommand(decision="APPROVED"), make_actor(es_admin=True)
    )

    assert resultado.afecta_turnos is None
    assert impacto.consultas == []


async def test_nadie_se_aprueba_a_si_mismo() -> None:
    empleado = make_empleado()
    ausencia = _pendiente(empleado.id)
    deps, _, _ = _deps(empleado, ausencia)

    with pytest.raises(OperacionNoPermitidaError):
        await DecidirAusencia(deps).execute(
            ausencia.id,
            DecidirAusenciaCommand(decision="APPROVED"),
            make_actor(empleado_id=empleado.id, sector_gestionado_id=empleado.department_id),
        )


async def test_jefe_de_otro_sector_no_decide() -> None:
    empleado = make_empleado()
    ausencia = _pendiente(empleado.id)
    deps, _, _ = _deps(empleado, ausencia)

    with pytest.raises(OperacionNoPermitidaError):
        await DecidirAusencia(deps).execute(
            ausencia.id,
            DecidirAusenciaCommand(decision="APPROVED"),
            make_actor(sector_gestionado_id=uuid.uuid4()),
        )
