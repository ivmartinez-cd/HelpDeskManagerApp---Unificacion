"""Round-trips de los repos de prestadores contra Postgres de test."""

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_historial_repository import (  # noqa: E501
    SqlAlchemyAsignacionHistorialRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_contacto_repository import (
    SqlAlchemyContactoRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)


async def _app_user(
    session: AsyncSession, *, full_name: str = "Ana Prueba", is_active: bool = True
) -> uuid.UUID:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.local",
        password_hash="x",
        full_name=full_name,
        is_active=is_active,
    )
    session.add(user)
    await session.flush()
    return user.id


def _prestador(
    den_comercial: str = "Rosario - PST SA",
    *,
    siges_id: int | None = None,
    is_active: bool = True,
) -> Prestador:
    return Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=siges_id if siges_id is not None else uuid.uuid4().int % 10_000_000,
        den_comercial=den_comercial,
        razon_social="PST SA",
        cuit="30-11111111-1",
        equipos=10,
        operador_id=None,
        is_active=is_active,
    )


async def test_prestador_round_trip_por_id_y_por_siges(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    prestador = _prestador(siges_id=137)
    await repo.add(prestador)

    por_id = await repo.get_by_id(prestador.id)
    assert por_id is not None and por_id.den_comercial == "Rosario - PST SA"
    por_siges = await repo.get_by_siges_empresa_id(137)
    assert por_siges is not None and por_siges.id == prestador.id
    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.get_by_siges_empresa_id(999_999_999) is None


async def test_prestador_list_all_filtra_inactivos_y_save_persiste(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    operador = await _app_user(db_session)
    activo = _prestador("Alfa - PST")
    baja = _prestador("Zeta - PST", is_active=False)
    await repo.add(activo)
    await repo.add(baja)

    assert [p.den_comercial for p in await repo.list_all()] == ["Alfa - PST"]
    todos = await repo.list_all(include_inactive=True)
    assert [p.den_comercial for p in todos] == ["Alfa - PST", "Zeta - PST"]

    activo.den_comercial = "Alfa Norte - PST"
    activo.operador_id = operador
    await repo.save(activo)
    guardado = await repo.get_by_id(activo.id)
    assert guardado is not None
    assert guardado.den_comercial == "Alfa Norte - PST"
    assert guardado.operador_id == operador
    await repo.save(_prestador())  # save de un id inexistente es no-op


def _contacto(
    prestador_id: uuid.UUID, nombre: str, *, sort_order: int = 0
) -> ContactoPrestador:
    return ContactoPrestador(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        nombre=nombre,
        telefono="341-5555555",
        email="c@pst.com.ar",
        is_principal=False,
        sort_order=sort_order,
    )


async def test_contactos_round_trip_orden_y_agrupado(db_session: AsyncSession) -> None:
    prestadores = SqlAlchemyPrestadorRepository(db_session)
    repo = SqlAlchemyContactoRepository(db_session)
    uno = _prestador("Uno - PST")
    dos = _prestador("Dos - PST")
    await prestadores.add(uno)
    await prestadores.add(dos)
    segundo = _contacto(uno.id, "Beto", sort_order=2)
    primero = _contacto(uno.id, "Ana", sort_order=1)
    del_otro = _contacto(dos.id, "Caro")
    for c in (segundo, primero, del_otro):
        await repo.add(c)

    assert [c.nombre for c in await repo.list_by_prestador(uno.id)] == ["Ana", "Beto"]
    agrupados = await repo.list_by_prestadores([uno.id, dos.id])
    assert {p: [c.nombre for c in cs] for p, cs in agrupados.items()} == {
        uno.id: ["Ana", "Beto"],
        dos.id: ["Caro"],
    }
    assert await repo.list_by_prestadores([]) == {}


async def test_contacto_get_save_y_delete(db_session: AsyncSession) -> None:
    prestadores = SqlAlchemyPrestadorRepository(db_session)
    repo = SqlAlchemyContactoRepository(db_session)
    prestador = _prestador()
    await prestadores.add(prestador)
    contacto = _contacto(prestador.id, "Ana")
    await repo.add(contacto)

    contacto.nombre = "Ana María"
    contacto.is_principal = True
    await repo.save(contacto)
    guardado = await repo.get_by_id(contacto.id)
    assert guardado is not None and guardado.nombre == "Ana María" and guardado.is_principal

    await repo.delete(contacto.id)
    assert await repo.get_by_id(contacto.id) is None
    await repo.save(contacto)  # no-op sobre id borrado


async def test_historial_reasignar_cierra_el_tramo_abierto(db_session: AsyncSession) -> None:
    prestadores = SqlAlchemyPrestadorRepository(db_session)
    repo = SqlAlchemyAsignacionHistorialRepository(db_session)
    prestador = _prestador()
    await prestadores.add(prestador)
    juan = await _app_user(db_session, full_name="Juan")
    pedro = await _app_user(db_session, full_name="Pedro")

    await repo.reasignar(prestador.id, juan, date(2026, 1, 1))
    await repo.reasignar(prestador.id, pedro, date(2026, 6, 1))

    tramos = sorted(await repo.list_by_prestador(prestador.id), key=lambda t: t.desde)
    assert [(t.operador_id, t.hasta) for t in tramos] == [
        (juan, date(2026, 5, 31)),
        (pedro, None),
    ]


async def test_historial_borra_tramos_que_nunca_cubrieron_un_dia(
    db_session: AsyncSession,
) -> None:
    prestadores = SqlAlchemyPrestadorRepository(db_session)
    repo = SqlAlchemyAsignacionHistorialRepository(db_session)
    prestador = _prestador()
    await prestadores.add(prestador)
    juan = await _app_user(db_session, full_name="Juan")
    pedro = await _app_user(db_session, full_name="Pedro")

    # Mismo día: cerrar el tramo de Juan daría hasta < desde → se borra.
    await repo.reasignar(prestador.id, juan, date(2026, 8, 14))
    await repo.reasignar(prestador.id, pedro, date(2026, 8, 14))

    tramos = await repo.list_by_prestador(prestador.id)
    assert [(t.operador_id, t.hasta) for t in tramos] == [(pedro, None)]


def _override(
    *,
    ausente: uuid.UUID,
    reemplazante: uuid.UUID,
    creador: uuid.UUID,
    alcance: frozenset[uuid.UUID] | None = None,
) -> AsignacionOverride:
    return AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 31),
        alcance="TOTAL" if alcance is None else alcance,
        estado="ACTIVA",
        motivo="vacaciones",
        created_by_user_id=creador,
    )


async def test_override_total_round_trip_y_cancelacion(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    juan = await _app_user(db_session, full_name="Juan")
    pedro = await _app_user(db_session, full_name="Pedro")
    override = _override(ausente=juan, reemplazante=pedro, creador=pedro)
    await repo.create(override)

    leido = await repo.get_by_id(override.id)
    assert leido is not None and leido.alcance == "TOTAL" and leido.estado == "ACTIVA"
    assert [o.id for o in await repo.list_all()] == [override.id]
    assert [o.id for o in await repo.list_activos_por_ausente(juan)] == [override.id]
    assert [o.id for o in await repo.list_activos_por_reemplazante(pedro)] == [override.id]

    await repo.cancelar(override.id)
    cancelado = await repo.get_by_id(override.id)
    assert cancelado is not None and cancelado.estado == "CANCELADA"
    assert await repo.list_activos_por_ausente(juan) == []
    await repo.cancelar(uuid.uuid4())  # id inexistente: no-op


async def test_override_parcial_persiste_el_alcance_por_prestador(
    db_session: AsyncSession,
) -> None:
    prestadores = SqlAlchemyPrestadorRepository(db_session)
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    prestador = _prestador()
    await prestadores.add(prestador)
    juan = await _app_user(db_session, full_name="Juan")
    pedro = await _app_user(db_session, full_name="Pedro")
    override = _override(
        ausente=juan, reemplazante=pedro, creador=pedro, alcance=frozenset({prestador.id})
    )
    await repo.create(override)

    leido = await repo.get_by_id(override.id)
    assert leido is not None and leido.alcance == frozenset({prestador.id})
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_user_provider_resuelve_ids_y_lista_activos(db_session: AsyncSession) -> None:
    provider = SqlAlchemyUserProvider(db_session)
    ana = await _app_user(db_session, full_name="Ana")
    await _app_user(db_session, full_name="Baja", is_active=False)

    assert await provider.get_users_by_ids([]) == {}
    assert (await provider.get_users_by_ids([ana]))[ana].full_name == "Ana"
    activos = [u.full_name for u in await provider.list_all_active_users()]
    assert "Ana" in activos and "Baja" not in activos
