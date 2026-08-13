import uuid

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import SetPrestadorActiveCommand
from src.modules.prestadores.application.use_cases.deactivate_prestador import (
    SetPrestadorActive,
    SetPrestadorActiveDependencies,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from tests.unit.domain.prestadores.fakes import FakePrestadorRepository


async def test_baja_conserva_el_operador_para_una_futura_reactivacion() -> None:
    prestadores = FakePrestadorRepository()
    operador_id = uuid.uuid4()
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Rosario",
        razon_social=None,
        cuit=None,
        operador_id=operador_id,
        is_active=True,
    )
    prestadores.rows[prestador.id] = prestador

    deps = SetPrestadorActiveDependencies(prestadores=prestadores)
    await SetPrestadorActive(deps).execute(
        SetPrestadorActiveCommand(prestador_id=prestador.id, is_active=False)
    )

    guardado = prestadores.rows[prestador.id]
    assert guardado.is_active is False
    assert guardado.operador_id == operador_id


async def test_prestador_inexistente_lanza_not_found() -> None:
    deps = SetPrestadorActiveDependencies(prestadores=FakePrestadorRepository())
    with pytest.raises(PrestadorNotFoundError):
        await SetPrestadorActive(deps).execute(
            SetPrestadorActiveCommand(prestador_id=uuid.uuid4(), is_active=False)
        )
