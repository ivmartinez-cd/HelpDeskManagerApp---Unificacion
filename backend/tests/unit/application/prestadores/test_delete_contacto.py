import uuid

import pytest

from src.modules.prestadores.application.use_cases.delete_contacto import (
    DeleteContacto,
    DeleteContactoDependencies,
)
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.errors import ContactoNotFoundError
from tests.unit.domain.prestadores.fakes import FakeContactoRepository


async def test_borra_el_contacto_existente() -> None:
    contactos = FakeContactoRepository()
    contacto = ContactoPrestador(
        id=uuid.uuid4(),
        prestador_id=uuid.uuid4(),
        nombre="Juan",
        telefono=None,
        email=None,
        is_principal=False,
        sort_order=0,
    )
    contactos.rows[contacto.id] = contacto

    await DeleteContacto(DeleteContactoDependencies(contactos=contactos)).execute(contacto.id)

    assert contacto.id not in contactos.rows


async def test_contacto_inexistente_lanza_not_found() -> None:
    deps = DeleteContactoDependencies(contactos=FakeContactoRepository())
    with pytest.raises(ContactoNotFoundError):
        await DeleteContacto(deps).execute(uuid.uuid4())
