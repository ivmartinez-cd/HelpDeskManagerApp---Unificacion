import uuid

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import UpsertContactoCommand
from src.modules.prestadores.application.use_cases.upsert_contacto import (
    UpsertContacto,
    UpsertContactoDependencies,
)
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.errors import ContactoNotFoundError
from tests.unit.domain.prestadores.fakes import FakeContactoRepository


async def test_crea_un_contacto_nuevo_cuando_no_se_pasa_contacto_id() -> None:
    contactos = FakeContactoRepository()
    prestador_id = uuid.uuid4()

    use_case = UpsertContacto(UpsertContactoDependencies(contactos=contactos))
    dto = await use_case.execute(
        UpsertContactoCommand(
            contacto_id=None,
            prestador_id=prestador_id,
            nombre="David Maldonado",
            telefono="54 9 2644 14-5930",
            email="davidhugomaldonado@gmail.com",
            is_principal=True,
        )
    )

    assert len(contactos.rows) == 1
    assert dto.nombre == "David Maldonado"
    assert dto.prestador_id == prestador_id


async def test_edita_un_contacto_existente_preservando_su_prestador() -> None:
    contactos = FakeContactoRepository()
    prestador_id = uuid.uuid4()
    existente = ContactoPrestador(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        nombre="Nombre viejo",
        telefono=None,
        email=None,
        is_principal=False,
        sort_order=0,
    )
    contactos.rows[existente.id] = existente

    use_case = UpsertContacto(UpsertContactoDependencies(contactos=contactos))
    dto = await use_case.execute(
        UpsertContactoCommand(
            contacto_id=existente.id,
            prestador_id=uuid.uuid4(),  # se ignora -- el prestador no cambia al editar
            nombre="Nombre nuevo",
            telefono="54 9 1111 11-1111",
            email="nuevo@example.com",
        )
    )

    assert len(contactos.rows) == 1
    assert dto.prestador_id == prestador_id
    assert dto.nombre == "Nombre nuevo"


async def test_editar_contacto_inexistente_lanza_not_found() -> None:
    use_case = UpsertContacto(UpsertContactoDependencies(contactos=FakeContactoRepository()))
    with pytest.raises(ContactoNotFoundError):
        await use_case.execute(
            UpsertContactoCommand(
                contacto_id=uuid.uuid4(),
                prestador_id=uuid.uuid4(),
                nombre="X",
                telefono=None,
                email=None,
            )
        )
