from datetime import date

from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GetPuntajesPeriodoRequest,
)
from src.modules.bono_tecnicos.application.use_cases.get_puntajes_periodo import (
    GetPuntajesPeriodo,
)
from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from tests.unit.application.bono_tecnicos.fakes import (
    FakeBonoTecnicoInputRepository,
    FakeConteoTecnicoGateway,
    FakeDiasSugeridosGateway,
    FakeSolicitudTvRepository,
    build_conteo,
    build_solicitud_tv,
)


def _use_case(
    conteos=None, inputs=None, dias_sugeridos=None, solicitudes_tv=None
) -> GetPuntajesPeriodo:
    return GetPuntajesPeriodo(
        FakeConteoTecnicoGateway(conteos or []),
        FakeBonoTecnicoInputRepository(inputs or []),
        FakeDiasSugeridosGateway(dias_sugeridos or {}),
        FakeSolicitudTvRepository(solicitudes_tv or []),
    )


async def test_sin_conteos_devuelve_lista_vacia() -> None:
    use_case = _use_case()

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert result == []


async def test_sin_input_cargado_el_puntaje_queda_null() -> None:
    conteo = build_conteo("CD - Ana", id_tecnico=1, correctivo=5)
    use_case = _use_case(conteos=[conteo])

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert len(result) == 1
    assert result[0].dias == 0
    assert result[0].tareas_varias == 0
    assert result[0].puntaje is None


async def test_combina_conteo_input_y_solicitudes_tv_aprobadas_para_calcular_el_puntaje() -> None:
    conteo = build_conteo(
        "CD - Agustin HACZEK",
        id_tecnico=1314,
        periodo=202605,
        correctivo=47,
        preventivo=44,
        inst_des=4,
        pre_correctivo=1,
        entrega_insumos=22,
    )
    input_ = BonoTecnicoInput(
        id_tecnico=1314, periodo=202605, tecnico="CD - Agustin HACZEK", dias=17
    )
    solicitudes = [
        build_solicitud_tv(
            id_tecnico=1314, fecha=date(2026, 5, d), estado=EstadoSolicitudTv.APROBADA
        )
        for d in range(1, 26)
    ]
    use_case = _use_case(conteos=[conteo], inputs=[input_], solicitudes_tv=solicitudes)

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert len(result) == 1
    dto = result[0]
    assert dto.dias == 17
    assert dto.tareas_varias == 25
    assert dto.puntaje == 7.48


async def test_solicitudes_pendientes_o_rechazadas_no_suman_tv() -> None:
    conteo = build_conteo("CD - Ana", id_tecnico=1, correctivo=5)
    input_ = BonoTecnicoInput(id_tecnico=1, periodo=202605, tecnico="CD - Ana", dias=10)
    solicitudes = [
        build_solicitud_tv(id_tecnico=1, estado=EstadoSolicitudTv.PENDIENTE),
        build_solicitud_tv(id_tecnico=1, estado=EstadoSolicitudTv.RECHAZADA),
    ]
    use_case = _use_case(conteos=[conteo], inputs=[input_], solicitudes_tv=solicitudes)

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert result[0].tareas_varias == 0


async def test_ignora_input_de_otro_tecnico() -> None:
    conteo = build_conteo("CD - Ana", id_tecnico=1, correctivo=5)
    input_de_otro = BonoTecnicoInput(id_tecnico=2, periodo=202605, tecnico="CD - Beto", dias=20)
    use_case = _use_case(conteos=[conteo], inputs=[input_de_otro])

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert result[0].dias == 0
    assert result[0].puntaje is None


async def test_sin_tecnico_vinculado_dias_sugeridos_es_null() -> None:
    conteo = build_conteo("CD - Ana", id_tecnico=1, correctivo=5)
    use_case = _use_case(conteos=[conteo], dias_sugeridos={})

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert result[0].dias_sugeridos is None


async def test_tecnico_vinculado_expone_dias_sugeridos() -> None:
    conteo = build_conteo("CD - Ana", id_tecnico=1, correctivo=5)
    use_case = _use_case(conteos=[conteo], dias_sugeridos={1: 19})

    result = await use_case.execute(GetPuntajesPeriodoRequest(periodo=202605))

    assert result[0].dias_sugeridos == 19
