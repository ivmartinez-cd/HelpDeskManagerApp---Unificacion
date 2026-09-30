"""El certificado de una baja (dato de salud) lo ven el dueño, el jefe de su
sector o un admin; nadie más, aunque tenga el id."""

import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.vacaciones.application.use_cases.adjuntar_certificado_ausencia import (
    ObtenerCertificadoAusencia,
)
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.errors import OperacionNoPermitidaError
from tests.unit.application.vacaciones.fakes import FakeAusenciaRepo, FakeEmpleadoRepo
from tests.unit.domain.vacaciones.factories import make_actor, make_empleado

_EMPLEADO = make_empleado()


def _caso() -> tuple[ObtenerCertificadoAusencia, uuid.UUID]:
    ausencia = Ausencia(
        id=uuid.uuid4(),
        empleado_id=_EMPLEADO.id,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 3),
        days_count=3,
        half_day=False,
        tipo=TipoAusencia.BAJA_ENFERMEDAD,
        reason="Gripe",
        status=EstadoSolicitud.APPROVED,
        created_at=datetime.now(UTC),
        certificado_filename="abc.pdf",
    )
    caso = ObtenerCertificadoAusencia(FakeAusenciaRepo([ausencia]), FakeEmpleadoRepo([_EMPLEADO]))
    return caso, ausencia.id


@pytest.mark.parametrize(
    "actor",
    [
        make_actor(empleado_id=_EMPLEADO.id),
        make_actor(sector_gestionado_id=_EMPLEADO.department_id),
        make_actor(es_admin=True),
    ],
    ids=["dueno", "jefe_del_sector", "admin"],
)
async def test_dueno_jefe_y_admin_ven_el_certificado(actor) -> None:
    caso, ausencia_id = _caso()

    assert await caso.execute(ausencia_id, actor) == "abc.pdf"


@pytest.mark.parametrize(
    "actor",
    [make_actor(empleado_id=uuid.uuid4()), make_actor(sector_gestionado_id=uuid.uuid4())],
    ids=["otro_empleado", "jefe_de_otro_sector"],
)
async def test_los_demas_no_ven_el_certificado(actor) -> None:
    caso, ausencia_id = _caso()

    with pytest.raises(OperacionNoPermitidaError):
        await caso.execute(ausencia_id, actor)
