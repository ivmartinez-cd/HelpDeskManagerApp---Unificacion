import uuid

import pytest

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    DecidirSolicitudTvRequest,
)
from src.modules.bono_tecnicos.application.use_cases.decidir_solicitud_tv import (
    DecidirSolicitudTv,
)
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.bono_tecnicos.domain.errors import SolicitudTvNoEncontradaError
from tests.unit.application.bono_tecnicos.fakes import FakeSolicitudTvRepository, build_solicitud_tv


async def test_aprobar_cambia_el_estado() -> None:
    solicitud = build_solicitud_tv()
    repo = FakeSolicitudTvRepository([solicitud])
    use_case = DecidirSolicitudTv(repo)

    dto = await use_case.execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud.id,
            decision="APROBADA",
            resuelta_por_email="supervisor@canaldirecto.com.ar",
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
    use_case = DecidirSolicitudTv(repo)

    dto = await use_case.execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud.id,
            decision="RECHAZADA",
            resuelta_por_email="supervisor@canaldirecto.com.ar",
            motivo="Tarea duplicada",
        )
    )

    assert dto.estado == EstadoSolicitudTv.RECHAZADA.value
    assert dto.motivo_rechazo == "Tarea duplicada"


async def test_solicitud_inexistente_lanza_error() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = DecidirSolicitudTv(repo)

    with pytest.raises(SolicitudTvNoEncontradaError):
        await use_case.execute(
            DecidirSolicitudTvRequest(
                solicitud_id=uuid.uuid4(),
                decision="APROBADA",
                resuelta_por_email="supervisor@canaldirecto.com.ar",
            )
        )


async def test_permite_re_decidir_una_solicitud_ya_resuelta() -> None:
    solicitud = build_solicitud_tv(estado=EstadoSolicitudTv.RECHAZADA)
    repo = FakeSolicitudTvRepository([solicitud])
    use_case = DecidirSolicitudTv(repo)

    dto = await use_case.execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud.id,
            decision="APROBADA",
            resuelta_por_email="supervisor@canaldirecto.com.ar",
        )
    )

    assert dto.estado == EstadoSolicitudTv.APROBADA.value
