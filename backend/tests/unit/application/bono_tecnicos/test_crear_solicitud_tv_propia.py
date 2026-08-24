import uuid
from datetime import date

import pytest

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvPropiaRequest,
)
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv import CrearSolicitudTv
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv_propia import (
    CrearSolicitudTvPropia,
)
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoVinculado,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from tests.unit.application.bono_tecnicos.fakes import (
    FakeSolicitudTvRepository,
    FakeTecnicoIdentityGateway,
)


def _request(user_id: uuid.UUID) -> CrearSolicitudTvPropiaRequest:
    return CrearSolicitudTvPropiaRequest(
        user_id=user_id,
        fecha=date(2026, 5, 18),
        razon_social="Exolgan",
        sucursal="Dock Sur",
        tarea_realizada="Se buscan toner en Drago y se llevan a Exolgan.",
    )


async def test_resuelve_el_tecnico_del_vinculo_y_crea_la_solicitud() -> None:
    user_id = uuid.uuid4()
    identity_gateway = FakeTecnicoIdentityGateway(
        {user_id: TecnicoVinculado(id_tecnico=1314, tecnico="Agustin Haczek")}
    )
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTvPropia(identity_gateway, CrearSolicitudTv(repo))

    dto = await use_case.execute(_request(user_id))

    assert dto.id_tecnico == 1314
    assert dto.tecnico == "Agustin Haczek"


async def test_usuario_sin_vinculo_lanza_error_y_no_crea_nada() -> None:
    user_id = uuid.uuid4()
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTvPropia(FakeTecnicoIdentityGateway(), CrearSolicitudTv(repo))

    with pytest.raises(TecnicoNoVinculadoError):
        await use_case.execute(_request(user_id))

    assert await repo.list_by_periodo(Periodo(202605)) == []
