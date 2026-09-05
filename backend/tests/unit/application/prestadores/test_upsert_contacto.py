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


def _contacto(prestador_id: uuid.UUID, nombre: str, *, principal: bool) -> ContactoPrestador:
    return ContactoPrestador(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        nombre=nombre,
        telefono=None,
        email=None,
        is_principal=principal,
        sort_order=0,
    )


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
    existente = _contacto(prestador_id, "Nombre viejo", principal=False)
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


async def test_marcar_principal_desmarca_al_anterior_del_mismo_prestador() -> None:
    contactos = FakeContactoRepository()
    prestador_id = uuid.uuid4()
    anterior = _contacto(prestador_id, "Anterior", principal=True)
    de_otro_pst = _contacto(uuid.uuid4(), "Otro PST", principal=True)
    contactos.rows[anterior.id] = anterior
    contactos.rows[de_otro_pst.id] = de_otro_pst

    use_case = UpsertContacto(UpsertContactoDependencies(contactos=contactos))
    dto = await use_case.execute(
        UpsertContactoCommand(
            contacto_id=None,
            prestador_id=prestador_id,
            nombre="Nuevo principal",
            telefono=None,
            email=None,
            is_principal=True,
        )
    )

    principales = [c for c in await contactos.list_by_prestador(prestador_id) if c.is_principal]
    assert [c.id for c in principales] == [dto.id]
    assert contactos.rows[de_otro_pst.id].is_principal is True


async def test_editar_sin_principal_no_toca_a_los_demas() -> None:
    contactos = FakeContactoRepository()
    prestador_id = uuid.uuid4()
    principal = _contacto(prestador_id, "Principal", principal=True)
    secundario = _contacto(prestador_id, "Secundario", principal=False)
    contactos.rows[principal.id] = principal
    contactos.rows[secundario.id] = secundario

    await UpsertContacto(UpsertContactoDependencies(contactos=contactos)).execute(
        UpsertContactoCommand(
            contacto_id=secundario.id,
            prestador_id=prestador_id,
            nombre="Secundario renombrado",
            telefono=None,
            email=None,
            is_principal=False,
        )
    )

    assert contactos.rows[principal.id].is_principal is True
