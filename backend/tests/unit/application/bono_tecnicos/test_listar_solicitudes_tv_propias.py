import uuid
from datetime import date

import pytest

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    ListarSolicitudesTvPropiasRequest,
)
from src.modules.bono_tecnicos.application.use_cases.listar_solicitudes_tv_propias import (
    ListarSolicitudesTvPropias,
)
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from tests.unit.application.bono_tecnicos.fakes import (
    FakeSolicitudTvRepository,
    FakeTecnicoIdentityGateway,
    build_solicitud_tv,
)


async def test_lista_solo_las_del_tecnico_vinculado_al_usuario() -> None:
    user_id = uuid.uuid4()
    identity_gateway = FakeTecnicoIdentityGateway(
        {user_id: TecnicoVinculado(id_tecnico=1314, tecnico="Agustin Haczek")}
    )
    propia = build_solicitud_tv(id_tecnico=1314, fecha=date(2026, 5, 18))
    ajena = build_solicitud_tv(id_tecnico=999, fecha=date(2026, 5, 18))
    repo = FakeSolicitudTvRepository([propia, ajena])
    use_case = ListarSolicitudesTvPropias(identity_gateway, repo)

    result = await use_case.execute(
        ListarSolicitudesTvPropiasRequest(user_id=user_id, periodo=202605)
    )

    assert [s.id for s in result] == [propia.id]


async def test_usuario_sin_vinculo_lanza_error() -> None:
    use_case = ListarSolicitudesTvPropias(
        FakeTecnicoIdentityGateway(), FakeSolicitudTvRepository()
    )

    with pytest.raises(TecnicoNoVinculadoError):
        await use_case.execute(
            ListarSolicitudesTvPropiasRequest(user_id=uuid.uuid4(), periodo=202605)
        )
