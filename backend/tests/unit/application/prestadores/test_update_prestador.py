import uuid

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import UpdatePrestadorCommand
from src.modules.prestadores.application.use_cases.update_prestador import (
    UpdatePrestador,
    UpdatePrestadorDependencies,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from tests.unit.domain.prestadores.fakes import (
    FakeContactoRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)


def _deps(prestadores: FakePrestadorRepository) -> UpdatePrestadorDependencies:
    return UpdatePrestadorDependencies(
        prestadores=prestadores, contactos=FakeContactoRepository(), users=FakeUserProvider()
    )


async def test_edita_datos_propios_sin_tocar_operador_equipos_ni_is_active() -> None:
    prestadores = FakePrestadorRepository()
    operador_id = uuid.uuid4()
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="Nombre viejo",
        razon_social=None,
        cuit=None,
        equipos=841,
        operador_id=operador_id,
        is_active=False,
    )
    prestadores.rows[prestador.id] = prestador

    dto = await UpdatePrestador(_deps(prestadores)).execute(
        UpdatePrestadorCommand(
            prestador_id=prestador.id,
            den_comercial="Nombre nuevo",
            razon_social="Razón nueva",
            cuit="30-22222222-2",
        )
    )

    assert dto.den_comercial == "Nombre nuevo"
    assert dto.razon_social == "Razón nueva"
    # equipos ya no es editable: se preserva el último valor contado desde Siges
    assert dto.equipos == 841
    assert dto.operador_id == operador_id
    assert dto.is_active is False
    assert prestadores.rows[prestador.id].den_comercial == "Nombre nuevo"


async def test_prestador_inexistente_lanza_not_found() -> None:
    with pytest.raises(PrestadorNotFoundError):
        await UpdatePrestador(_deps(FakePrestadorRepository())).execute(
            UpdatePrestadorCommand(
                prestador_id=uuid.uuid4(),
                den_comercial="X",
                razon_social=None,
                cuit=None,
            )
        )
