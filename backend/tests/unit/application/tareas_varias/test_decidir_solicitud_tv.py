import uuid

import pytest

from src.modules.tareas_varias.application.dtos.solicitud_tv_dto import (
    DecidirSolicitudTvRequest,
)
from src.modules.tareas_varias.application.use_cases.decidir_solicitud_tv import (
    DecidirSolicitudTv,
)
from src.modules.tareas_varias.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.tareas_varias.domain.errors import (
    AutoaprobacionTvError,
    SolicitudTvNoEncontradaError,
)
from src.modules.tareas_varias.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from tests.unit.application.tareas_varias.fakes import (
    FakeSolicitudTvRepository,
    FakeTecnicoIdentityGateway,
    build_solicitud_tv,
)


async def test_aprobar_cambia_el_estado() -> None:
    solicitud = build_solicitud_tv()
    repo = FakeSolicitudTvRepository([solicitud])
    use_case = DecidirSolicitudTv(repo, FakeTecnicoIdentityGateway())

    dto = await use_case.execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud.id,
            decision="APROBADA",
            resuelta_por_email="supervisor@canaldirecto.com.ar",
            resuelta_por_user_id=uuid.uuid4(),
        )
    )

    assert dto.estado == EstadoSolicitudTv.APROBADA.value
    assert dto.resuelta_por_email == "supervisor@canaldirecto.com.ar"
    guardada = await repo.get_by_id(solicitud.id)
    assert guardada is not None
    assert guardada.estado is EstadoSolicitudTv.APROBADA


async def test_rechazar_guarda_el_motivo() -> None:
    solicitud = build_solicitud_tv()
    repo = FakeSolicitudTvRepository([solicitud])
    use_case = DecidirSolicitudTv(repo, FakeTecnicoIdentityGateway())

    dto = await use_case.execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud.id,
            decision="RECHAZADA",
            resuelta_por_email="supervisor@canaldirecto.com.ar",
            resuelta_por_user_id=uuid.uuid4(),
            motivo="Tarea duplicada",
        )
    )

    assert dto.estado == EstadoSolicitudTv.RECHAZADA.value
    assert dto.motivo_rechazo == "Tarea duplicada"


async def test_solicitud_inexistente_lanza_error() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = DecidirSolicitudTv(repo, FakeTecnicoIdentityGateway())

    with pytest.raises(SolicitudTvNoEncontradaError):
        await use_case.execute(
            DecidirSolicitudTvRequest(
                solicitud_id=uuid.uuid4(),
                decision="APROBADA",
                resuelta_por_email="supervisor@canaldirecto.com.ar",
            resuelta_por_user_id=uuid.uuid4(),
            )
        )


async def test_permite_re_decidir_una_solicitud_ya_resuelta() -> None:
    solicitud = build_solicitud_tv(estado=EstadoSolicitudTv.RECHAZADA)
    repo = FakeSolicitudTvRepository([solicitud])
    use_case = DecidirSolicitudTv(repo, FakeTecnicoIdentityGateway())

    dto = await use_case.execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud.id,
            decision="APROBADA",
            resuelta_por_email="supervisor@canaldirecto.com.ar",
            resuelta_por_user_id=uuid.uuid4(),
        )
    )

    assert dto.estado == EstadoSolicitudTv.APROBADA.value


async def test_el_supervisor_no_decide_sus_propias_tareas() -> None:
    solicitud = build_solicitud_tv(id_tecnico=1314)
    repo = FakeSolicitudTvRepository([solicitud])
    yo = uuid.uuid4()
    identidades = FakeTecnicoIdentityGateway({yo: TecnicoVinculado(1314, "CD - Yo")})

    with pytest.raises(AutoaprobacionTvError):
        await DecidirSolicitudTv(repo, identidades).execute(
            DecidirSolicitudTvRequest(
                solicitud_id=solicitud.id,
                decision="APROBADA",
                resuelta_por_email="yo@canaldirecto.com.ar",
                resuelta_por_user_id=yo,
            )
        )
    guardada = await repo.get_by_id(solicitud.id)
    assert guardada is not None and guardada.estado is EstadoSolicitudTv.PENDIENTE
