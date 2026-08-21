import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.contadores.domain.entities.cliente_nuevo import (
    ESTADO_CERRADO,
    ESTADO_STC_PENDIENTE,
    ClienteNuevo,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_cliente_nuevo_repository import (  # noqa: E501
    SqlAlchemyClienteNuevoRepository,
)


async def _crear_usuario(db_session: AsyncSession) -> uuid.UUID:
    user_id = uuid.uuid4()
    db_session.add(
        AppUser(
            id=user_id,
            email=f"tl-{user_id.hex[:8]}@canaldirecto.test",
            full_name="TL Contadores",
            password_hash="x",
            is_active=True,
            is_superadmin=False,
        )
    )
    await db_session.flush()
    return user_id


def _ficha(
    user_id: uuid.UUID, cliente: str = "EXPRESO BILETTA", **overrides: object
) -> ClienteNuevo:
    base: dict[str, object] = {
        "id": uuid.uuid4(),
        "cliente": cliente,
        "created_by_user_id": user_id,
        "siges_empresa_id": 1416,
        "contrato_nro": "SOD36CDSI00837",
        "fecha_firma": date(2026, 7, 28),
        "vendedor": "AV",
        "operador_id": "marodriguez",
        "equipos_previstos": 10,
        "fecha_estimada_primera_facturacion": date(2026, 10, 1),
    }
    base.update(overrides)
    return ClienteNuevo(**base)  # type: ignore[arg-type]


async def test_add_then_get_by_id_round_trips(db_session: AsyncSession) -> None:
    user_id = await _crear_usuario(db_session)
    repo = SqlAlchemyClienteNuevoRepository(db_session)
    ficha = _ficha(user_id)

    await repo.add(ficha)
    found = await repo.get_by_id(ficha.id)

    assert found is not None
    assert found.cliente == "EXPRESO BILETTA"
    assert found.siges_empresa_id == 1416
    assert found.fecha_firma == date(2026, 7, 28)
    assert found.estado == "ESPERANDO_INSTALACION"
    assert found.created_by_user_id == user_id


async def test_get_abierta_by_cliente_ignora_cerradas_y_mayusculas(
    db_session: AsyncSession,
) -> None:
    user_id = await _crear_usuario(db_session)
    repo = SqlAlchemyClienteNuevoRepository(db_session)
    await repo.add(_ficha(user_id, "SWEET DREAM", estado=ESTADO_CERRADO))
    assert await repo.get_abierta_by_cliente("sweet dream") is None

    abierta = _ficha(user_id, "SWEET DREAM")
    await repo.add(abierta)
    found = await repo.get_abierta_by_cliente("  sweet dream ")
    assert found is not None
    assert found.id == abierta.id


async def test_save_persists_changes_and_list_siges_ids(db_session: AsyncSession) -> None:
    user_id = await _crear_usuario(db_session)
    repo = SqlAlchemyClienteNuevoRepository(db_session)
    ficha = _ficha(user_id)
    await repo.add(ficha)
    await repo.add(_ficha(user_id, "BP", siges_empresa_id=None))

    ficha.estado = ESTADO_STC_PENDIENTE
    ficha.dia_corte = 25
    ficha.notas = "STC armado"
    await repo.save(ficha)

    found = await repo.get_by_id(ficha.id)
    assert found is not None
    assert found.estado == ESTADO_STC_PENDIENTE
    assert found.dia_corte == 25
    assert found.notas == "STC armado"
    assert await repo.list_siges_empresa_ids() == {1416}
    assert {f.cliente for f in await repo.list_all()} == {"EXPRESO BILETTA", "BP"}


async def test_delete_removes_row(db_session: AsyncSession) -> None:
    user_id = await _crear_usuario(db_session)
    repo = SqlAlchemyClienteNuevoRepository(db_session)
    ficha = _ficha(user_id)
    await repo.add(ficha)

    await repo.delete(ficha.id)

    assert await repo.get_by_id(ficha.id) is None
