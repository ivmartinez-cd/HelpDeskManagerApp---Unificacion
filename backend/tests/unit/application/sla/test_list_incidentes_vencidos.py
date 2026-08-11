import pytest

from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    ListIncidentesVencidos,
)
from src.modules.sla.domain.entities.incidente_sla import (
    RESULTADO_CORRECTO,
    RESULTADO_VENCIDO,
)
from src.modules.sla.domain.errors import PeriodoInvalidoError
from tests.unit.domain.sla.fakes import FakeSlaQueryGateway, build_incidente


async def test_filtra_solo_vencidos_preservando_el_orden_de_la_consulta() -> None:
    incidentes = [
        build_incidente(30, "CD - Ana", RESULTADO_VENCIDO),
        build_incidente(20, "CD - Beto", RESULTADO_CORRECTO),
        build_incidente(10, "PST Trelew", RESULTADO_VENCIDO),
    ]
    use_case = ListIncidentesVencidos(FakeSlaQueryGateway(incidentes))

    result = await use_case.execute(202608)

    assert [dto.id_incidente for dto in result] == [30, 10]


async def test_mapea_los_campos_del_incidente() -> None:
    incidente = build_incidente(42, "PST Trelew", RESULTADO_VENCIDO)
    use_case = ListIncidentesVencidos(FakeSlaQueryGateway([incidente]))

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
        await ListIncidentesVencidos(FakeSlaQueryGateway()).execute(202600)
