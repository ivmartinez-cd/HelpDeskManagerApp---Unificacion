from datetime import date

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import ListarSolicitudesTvRequest
from src.modules.bono_tecnicos.application.use_cases.listar_solicitudes_tv import (
    ListarSolicitudesTv,
)
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from tests.unit.application.bono_tecnicos.fakes import FakeSolicitudTvRepository, build_solicitud_tv


async def test_lista_solo_el_periodo_pedido() -> None:
    de_mayo = build_solicitud_tv(fecha=date(2026, 5, 18))
    de_junio = build_solicitud_tv(fecha=date(2026, 6, 2))
    repo = FakeSolicitudTvRepository([de_mayo, de_junio])
    use_case = ListarSolicitudesTv(repo)

    result = await use_case.execute(ListarSolicitudesTvRequest(periodo=202605))

    assert [s.id for s in result] == [de_mayo.id]


async def test_filtra_por_estado() -> None:
    pendiente = build_solicitud_tv(estado=EstadoSolicitudTv.PENDIENTE)
    aprobada = build_solicitud_tv(estado=EstadoSolicitudTv.APROBADA)
    repo = FakeSolicitudTvRepository([pendiente, aprobada])
    use_case = ListarSolicitudesTv(repo)

    result = await use_case.execute(
        ListarSolicitudesTvRequest(periodo=202605, estado="PENDIENTE")
    )

    assert [s.id for s in result] == [pendiente.id]


async def test_filtra_por_tecnico() -> None:
    de_ana = build_solicitud_tv(id_tecnico=1)
    de_beto = build_solicitud_tv(id_tecnico=2)
    repo = FakeSolicitudTvRepository([de_ana, de_beto])
    use_case = ListarSolicitudesTv(repo)

    result = await use_case.execute(ListarSolicitudesTvRequest(periodo=202605, id_tecnico=1))

    assert [s.id for s in result] == [de_ana.id]
