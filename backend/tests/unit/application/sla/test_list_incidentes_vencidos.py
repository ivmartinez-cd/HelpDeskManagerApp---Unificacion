import pytest

from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    AGENTE_LOCAL,
    AGENTE_SIN_OPERADOR,
    ListIncidentesVencidos,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.entities.incidente_sla import (
    RESULTADO_CORRECTO,
    RESULTADO_VENCIDO,
)
from src.modules.sla.domain.errors import PeriodoInvalidoError
from tests.unit.application.sla.fakes_pendientes import FakePrestadorLookup
from tests.unit.domain.sla.fakes import (
    FakeSlaQueryGateway,
    FakeSlaSnapshotRepository,
    build_incidente,
)


def _build_use_case(
    gateway: FakeSlaQueryGateway, lookup: FakePrestadorLookup | None = None
) -> ListIncidentesVencidos:
    repo = FakeSlaSnapshotRepository()
    return ListIncidentesVencidos(
        repo, RefreshSlaSnapshot(gateway, repo), lookup or FakePrestadorLookup()
    )


async def test_filtra_solo_vencidos_preservando_el_orden_de_la_consulta() -> None:
    incidentes = [
        build_incidente(30, "CD - Ana", RESULTADO_VENCIDO),
        build_incidente(20, "CD - Beto", RESULTADO_CORRECTO),
        build_incidente(10, "PST Trelew", RESULTADO_VENCIDO),
    ]
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(202608)

    assert [dto.id_incidente for dto in result] == [30, 10]


async def test_mapea_los_campos_del_incidente() -> None:
    incidente = build_incidente(42, "PST Trelew", RESULTADO_VENCIDO)
    use_case = _build_use_case(FakeSlaQueryGateway([incidente]))

    (dto,) = await use_case.execute(202608)

    assert dto.id_incidente == 42
    assert dto.tecnico == "PST Trelew"
    assert dto.region == incidente.region
    assert dto.cliente == incidente.cliente
    assert dto.sla_horas == incidente.sla_horas
    assert dto.horas_vencido == incidente.horas_vencido
    assert dto.rango == incidente.rango


async def test_periodo_invalido_lanza_error() -> None:
    with pytest.raises(PeriodoInvalidoError):
        await _build_use_case(FakeSlaQueryGateway()).execute(202600)


async def test_filtro_por_siges_ids_deja_solo_esos_tecnicos() -> None:
    incidentes = [
        build_incidente(1, "PST Trelew", RESULTADO_VENCIDO, id_tecnico=100),
        build_incidente(2, "PST Zapala", RESULTADO_VENCIDO, id_tecnico=200),
        build_incidente(3, "PST Trelew", RESULTADO_VENCIDO, id_tecnico=100),
    ]
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(202608, siges_ids_filtro=[100])

    assert [dto.id_incidente for dto in result] == [1, 3]


async def test_agente_es_local_para_cd_y_operador_del_pst_para_el_resto() -> None:
    incidentes = [
        build_incidente(1, "CD", RESULTADO_VENCIDO, id_tecnico=100, region="LOCAL"),
        build_incidente(2, "PST Trelew", RESULTADO_VENCIDO, id_tecnico=200, region="INTERIOR"),
        build_incidente(3, "PST Sin Mapear", RESULTADO_VENCIDO, id_tecnico=300, region="INTERIOR"),
    ]
    lookup = FakePrestadorLookup(pst_to_operador={200: "Operador Sur"})
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes), lookup)

    result = await use_case.execute(202608)

    agentes = {dto.id_incidente: dto.agente for dto in result}
    assert agentes[1] == AGENTE_LOCAL
    assert agentes[2] == "Operador Sur"
    assert agentes[3] == AGENTE_SIN_OPERADOR


async def test_filtro_vacio_no_devuelve_ningun_incidente() -> None:
    incidentes = [build_incidente(1, "PST Trelew", RESULTADO_VENCIDO, id_tecnico=100)]
    use_case = _build_use_case(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(202608, siges_ids_filtro=[])

    assert result == []
