import uuid
from datetime import date, timedelta

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
    FakeAsignacionHistorialRepository,
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

    deps = GetPrestadorDependencies(
        prestadores=prestadores,
        contactos=contactos,
        users=users,
        asignaciones=FakeAsignacionHistorialRepository(),
    )
    dto = await GetPrestador(deps).execute(prestador.id)

    assert dto.operador_nombre == "Ana Pérez"
    assert dto.operador_color == "#ff6600"
    assert [c.nombre for c in dto.contactos] == ["Juan"]


async def test_el_operador_sale_del_historial_vigente_hoy_no_del_puntero() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    users = FakeUserProvider()
    puntero_id, vigente_id = uuid.uuid4(), uuid.uuid4()
    users.users[vigente_id] = UserInfo(id=vigente_id, full_name="Vigente Hoy")
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Rosario",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=puntero_id,
        is_active=True,
    )
    prestadores.rows[prestador.id] = prestador
    await asignaciones.reasignar(prestador.id, vigente_id, date.today() - timedelta(days=1))

    deps = GetPrestadorDependencies(
        prestadores=prestadores,
        contactos=FakeContactoRepository(),
        users=users,
        asignaciones=asignaciones,
    )
    dto = await GetPrestador(deps).execute(prestador.id)

    assert dto.operador_id == vigente_id
    assert dto.operador_nombre == "Vigente Hoy"


async def test_prestador_inexistente_lanza_not_found() -> None:
    deps = GetPrestadorDependencies(
        prestadores=FakePrestadorRepository(),
        contactos=FakeContactoRepository(),
        users=FakeUserProvider(),
        asignaciones=FakeAsignacionHistorialRepository(),
    )
    with pytest.raises(PrestadorNotFoundError):
        await GetPrestador(deps).execute(uuid.uuid4())
