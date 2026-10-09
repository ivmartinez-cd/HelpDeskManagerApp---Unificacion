import uuid

import pytest

from src.modules.bono_tecnicos.application.dtos.incidente_bono_dto import (
    GetMisIncidentesRequest,
)
from src.modules.bono_tecnicos.application.use_cases.get_incidentes_tecnico import (
    GetIncidentesTecnico,
)
from src.modules.bono_tecnicos.application.use_cases.get_mis_incidentes import (
    GetMisIncidentes,
)
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from tests.unit.application.bono_tecnicos.fakes import (
    FakeConteoTecnicoGateway,
    FakeTecnicoIdentityGateway,
    build_incidente,
)

_USER_ID = uuid.uuid4()


def _use_case(gateway: FakeConteoTecnicoGateway, *, vinculado: bool = True) -> GetMisIncidentes:
    vinculos = {_USER_ID: TecnicoVinculado(id_tecnico=1314, tecnico="Agustin Haczek")}
    return GetMisIncidentes(
        FakeTecnicoIdentityGateway(vinculos if vinculado else {}),
        GetIncidentesTecnico(gateway),
    )


async def test_consulta_los_incidentes_del_tecnico_vinculado_al_usuario() -> None:
    gateway = FakeConteoTecnicoGateway(incidentes=[build_incidente(834176)])

    result = await _use_case(gateway).execute(
        GetMisIncidentesRequest(user_id=_USER_ID, periodo=202610)
    )

    assert [i.id_incidente for i in result] == [834176]
    assert gateway.incidentes_consultados == [(Periodo(202610), 1314)]


async def test_usuario_sin_vinculo_lanza_error_sin_consultar_siges() -> None:
    gateway = FakeConteoTecnicoGateway()

    with pytest.raises(TecnicoNoVinculadoError):
        await _use_case(gateway, vinculado=False).execute(
            GetMisIncidentesRequest(user_id=_USER_ID, periodo=202610)
        )

    assert gateway.incidentes_consultados == []
