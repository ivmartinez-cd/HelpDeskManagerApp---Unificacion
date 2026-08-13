import uuid

import pytest

from src.modules.prestadores.application.use_cases.get_prestador import (
    GetPrestador,
    GetPrestadorDependencies,
)
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import PrestadorNotFoundError
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeContactoRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)


async def test_devuelve_detalle_con_contactos_y_operador_resuelto() -> None:
    prestadores = FakePrestadorRepository()
    contactos = FakeContactoRepository()
    users = FakeUserProvider()
    operador_id = uuid.uuid4()
    users.users[operador_id] = UserInfo(id=operador_id, full_name="Ana Pérez", color="#ff6600")
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Rosario",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=operador_id,
        is_active=True,
    )
    prestadores.rows[prestador.id] = prestador
    contacto = ContactoPrestador(
        id=uuid.uuid4(),
        prestador_id=prestador.id,
        nombre="Juan",
        telefono="341-5555555",
        email=None,
        is_principal=True,
        sort_order=0,
    )
    contactos.rows[contacto.id] = contacto

    deps = GetPrestadorDependencies(prestadores=prestadores, contactos=contactos, users=users)
    dto = await GetPrestador(deps).execute(prestador.id)

    assert dto.operador_nombre == "Ana Pérez"
    assert dto.operador_color == "#ff6600"
    assert [c.nombre for c in dto.contactos] == ["Juan"]


async def test_prestador_inexistente_lanza_not_found() -> None:
    deps = GetPrestadorDependencies(
        prestadores=FakePrestadorRepository(),
        contactos=FakeContactoRepository(),
        users=FakeUserProvider(),
    )
    with pytest.raises(PrestadorNotFoundError):
        await GetPrestador(deps).execute(uuid.uuid4())
