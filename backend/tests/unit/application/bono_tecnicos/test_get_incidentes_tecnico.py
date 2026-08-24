import pytest

from src.modules.bono_tecnicos.application.dtos.incidente_bono_dto import (
    GetIncidentesTecnicoRequest,
)
from src.modules.bono_tecnicos.application.use_cases.get_incidentes_tecnico import (
    GetIncidentesTecnico,
)
from src.modules.bono_tecnicos.domain.errors import PeriodoInvalidoError
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from tests.unit.application.bono_tecnicos.fakes import (
    FakeConteoTecnicoGateway,
    build_incidente,
)


async def test_sin_incidentes_devuelve_lista_vacia() -> None:
    use_case = GetIncidentesTecnico(FakeConteoTecnicoGateway())

    result = await use_case.execute(GetIncidentesTecnicoRequest(periodo=202605, id_tecnico=1314))

    assert result == []


async def test_mapea_los_incidentes_del_gateway_a_dto() -> None:
    incidente = build_incidente(834176, categoria="Correctivo", cliente="Aerolineas Argentinas")
    use_case = GetIncidentesTecnico(FakeConteoTecnicoGateway(incidentes=[incidente]))

    result = await use_case.execute(GetIncidentesTecnicoRequest(periodo=202605, id_tecnico=1314))

    assert len(result) == 1
    dto = result[0]
    assert dto.id_incidente == 834176
    assert dto.categoria == "Correctivo"
    assert dto.cliente == "Aerolineas Argentinas"


async def test_consulta_el_periodo_y_tecnico_pedidos() -> None:
    gateway = FakeConteoTecnicoGateway()

    await GetIncidentesTecnico(gateway).execute(
        GetIncidentesTecnicoRequest(periodo=202605, id_tecnico=1314)
    )

    assert gateway.incidentes_consultados == [(Periodo(202605), 1314)]


async def test_periodo_invalido_lanza_error_sin_consultar() -> None:
    gateway = FakeConteoTecnicoGateway()

    with pytest.raises(PeriodoInvalidoError):
        await GetIncidentesTecnico(gateway).execute(
            GetIncidentesTecnicoRequest(periodo=202613, id_tecnico=1314)
        )

    assert gateway.incidentes_consultados == []
