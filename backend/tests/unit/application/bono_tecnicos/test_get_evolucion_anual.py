from datetime import date

from src.modules.bono_tecnicos.application.dtos.evolucion_anual_dto import (
    GetEvolucionAnualRequest,
)
from src.modules.bono_tecnicos.application.use_cases.get_evolucion_anual import (
    GetEvolucionAnual,
    GetEvolucionAnualPorts,
)
from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from tests.unit.application.bono_tecnicos.fakes import (
    FakeBonoTecnicoInputRepository,
    FakeConteoTecnicoGateway,
    FakeSolicitudTvRepository,
    build_conteo,
    build_solicitud_tv,
)


def _use_case(
    conteos_anio=None, inputs=None, solicitudes_tv=None
) -> tuple[GetEvolucionAnual, FakeConteoTecnicoGateway]:
    conteo_gateway = FakeConteoTecnicoGateway(conteos_anio=conteos_anio or [])
    use_case = GetEvolucionAnual(
        GetEvolucionAnualPorts(
            conteo_gateway=conteo_gateway,
            input_repo=FakeBonoTecnicoInputRepository(inputs or []),
            solicitud_tv_repo=FakeSolicitudTvRepository(solicitudes_tv or []),
        )
    )
    return use_case, conteo_gateway


async def test_una_sola_consulta_anual_al_gateway_de_conteos() -> None:
    use_case, gateway = _use_case()

    await use_case.execute(GetEvolucionAnualRequest(anio=2026))

    assert gateway.anios_consultados == [2026]


async def test_sin_conteos_devuelve_lista_de_tecnicos_vacia() -> None:
    use_case, _ = _use_case()

    result = await use_case.execute(GetEvolucionAnualRequest(anio=2026))

    assert result.anio == 2026
    assert result.tecnicos == []
    assert result.equipo == []


async def test_arma_la_serie_de_12_meses_por_tecnico() -> None:
    conteo_mayo = build_conteo("CD - Ana", id_tecnico=1, periodo=202605, correctivo=10)
    input_mayo = BonoTecnicoInput(id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=10)
    use_case, _ = _use_case(conteos_anio=[conteo_mayo], inputs=[input_mayo])

    result = await use_case.execute(GetEvolucionAnualRequest(anio=2026))

    assert len(result.tecnicos) == 1
    tecnico = result.tecnicos[0]
    assert tecnico.tecnico == "CD - Ana"
    assert len(tecnico.puntos) == 12
    punto_mayo = next(p for p in tecnico.puntos if p.periodo == 202605)
    assert punto_mayo.puntaje == 1.0
    assert tecnico.puntaje_promedio == 1.0
    assert tecnico.incidentes_total == 10


async def test_suma_tv_solicitadas_y_aprobadas_del_anio() -> None:
    conteo_mayo = build_conteo("CD - Ana", id_tecnico=1, periodo=202605, correctivo=10)
    solicitudes = [
        build_solicitud_tv(
            id_tecnico=1, fecha=date(2026, 5, 5), estado=EstadoSolicitudTv.APROBADA
        ),
        build_solicitud_tv(
            id_tecnico=1, fecha=date(2026, 5, 6), estado=EstadoSolicitudTv.PENDIENTE
        ),
    ]
    use_case, _ = _use_case(conteos_anio=[conteo_mayo], solicitudes_tv=solicitudes)

    result = await use_case.execute(GetEvolucionAnualRequest(anio=2026))

    tecnico = result.tecnicos[0]
    assert tecnico.tv_solicitadas_total == 2
    assert tecnico.tv_aprobadas_total == 1


async def test_calcula_el_promedio_del_equipo() -> None:
    conteo_ana = build_conteo("CD - Ana", id_tecnico=1, periodo=202605, correctivo=10)
    conteo_beto = build_conteo("CD - Beto", id_tecnico=2, periodo=202605, correctivo=20)
    inputs = [
        BonoTecnicoInput(id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=10),
        BonoTecnicoInput(id_tecnico=2, periodo=202605, tecnico="CD - Beto", dias=10),
    ]
    use_case, _ = _use_case(conteos_anio=[conteo_ana, conteo_beto], inputs=inputs)

    result = await use_case.execute(GetEvolucionAnualRequest(anio=2026))

    punto_mayo = next(p for p in result.equipo if p.periodo == 202605)
    assert punto_mayo.puntaje == 1.5
