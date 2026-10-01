"""Usuario → técnico de Siges por el vínculo de la ficha (vacaciones). El mismo
adapter existe en tareas_varias y en bono_tecnicos (cada módulo su puerto)."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.infrastructure.vacaciones.sqlalchemy_tecnico_identity_gateway import (  # noqa: E501
    SqlAlchemyTecnicoIdentityGateway as GatewayBono,
)
from src.modules.tareas_varias.infrastructure.vacaciones.sqlalchemy_tecnico_identity_gateway import (  # noqa: E501
    SqlAlchemyTecnicoIdentityGateway as GatewayTareas,
)
from tests.integration.infrastructure.personas.conftest import alta_empleado, crear_usuario

_GATEWAYS = [GatewayTareas, GatewayBono]


@pytest.mark.parametrize("gateway", _GATEWAYS, ids=["tareas_varias", "bono_tecnicos"])
async def test_resuelve_el_tecnico_de_la_ficha_vinculada(
    gateway: type, db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    user_id = await crear_usuario(db_session)
    await alta_empleado(
        db_session, sector_id, cargo_id, user_id=user_id, siges_empresa_id=1314,
        first_name="Agustin", last_name="Haczek",
    )

    vinculo = await gateway(db_session).get_por_usuario(user_id)

    assert vinculo is not None
    assert (vinculo.id_tecnico, vinculo.tecnico) == (1314, "Agustin Haczek")


@pytest.mark.parametrize("gateway", _GATEWAYS, ids=["tareas_varias", "bono_tecnicos"])
async def test_sin_ficha_o_sin_id_de_siges_es_none(
    gateway: type, db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    sin_siges = await crear_usuario(db_session)
    await alta_empleado(db_session, sector_id, cargo_id, user_id=sin_siges)

    assert await gateway(db_session).get_por_usuario(uuid.uuid4()) is None
    assert await gateway(db_session).get_por_usuario(sin_siges) is None
