"""SqlAlchemyNotificacionRepository contra Postgres real: publicar idempotente
por clave, visibilidad por audiencia y lectura por usuario."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.notificaciones.domain.entities.notificacion import NuevaNotificacion
from src.modules.notificaciones.infrastructure.repositories.sqlalchemy_notificacion_repository import (  # noqa: E501
    SqlAlchemyNotificacionRepository,
)

_SLA = "funcion:sla-avisos-mesa-ayuda"
_OTRA = "permiso:liquidaciones.view"


async def _usuario(db: AsyncSession) -> uuid.UUID:
    user = AppUser(
        email=f"{uuid.uuid4()}@test.local", full_name="Notif", password_hash="x",
        is_superadmin=False,
    )
    db.add(user)
    await db.flush()
    return user.id


def _nueva(clave: str, audiencia: str = _SLA) -> NuevaNotificacion:
    return NuevaNotificacion(clave=clave, audiencia=audiencia, titulo=clave, cuerpo="c", url="/x")


async def _sembrar(db: AsyncSession) -> SqlAlchemyNotificacionRepository:
    repo = SqlAlchemyNotificacionRepository(db)
    await repo.publicar([_nueva("a"), _nueva("b"), _nueva("otra", _OTRA)])
    return repo


async def _total(
    repo: SqlAlchemyNotificacionRepository, usuario: uuid.UUID, audiencias: frozenset[str] | None
) -> int:
    _, total = await repo.listar(usuario, audiencias, solo_no_leidas=False, offset=0, limit=10)
    return total


async def test_publicar_la_misma_clave_dos_veces_no_duplica(db_session: AsyncSession) -> None:
    repo = await _sembrar(db_session)
    await repo.publicar([_nueva("a"), _nueva("c")])

    items, total = await repo.listar(
        await _usuario(db_session), frozenset({_SLA}), solo_no_leidas=False, offset=0, limit=10
    )
    assert total == 3
    assert sorted(n.titulo for n in items) == ["a", "b", "c"]


async def test_cada_usuario_ve_solo_su_audiencia_y_el_superadmin_todas(
    db_session: AsyncSession,
) -> None:
    repo = await _sembrar(db_session)
    usuario = await _usuario(db_session)

    mias = await _total(repo, usuario, frozenset({_OTRA}))
    ninguna = await _total(repo, usuario, frozenset())
    todas = await _total(repo, usuario, None)
    assert (mias, ninguna, todas) == (1, 0, 3)


async def test_la_lectura_es_por_usuario(db_session: AsyncSession) -> None:
    repo = await _sembrar(db_session)
    ana, beto = await _usuario(db_session), await _usuario(db_session)
    visibles = frozenset({_SLA})

    items, _ = await repo.listar(ana, visibles, solo_no_leidas=True, offset=0, limit=10)
    una = next(n.id for n in items if n.titulo == "a")
    assert await repo.marcar_leidas(ana, visibles, [una]) == 1
    assert await repo.marcar_leidas(ana, visibles, [una]) == 0

    _, no_leidas_ana = await repo.listar(ana, visibles, solo_no_leidas=True, offset=0, limit=10)
    _, no_leidas_beto = await repo.listar(beto, visibles, solo_no_leidas=True, offset=0, limit=10)
    assert (no_leidas_ana, no_leidas_beto) == (1, 2)


async def test_marcar_todas_solo_toca_las_visibles(db_session: AsyncSession) -> None:
    repo = await _sembrar(db_session)
    usuario = await _usuario(db_session)

    assert await repo.marcar_leidas(usuario, frozenset({_SLA}), None) == 2
    _, pendientes = await repo.listar(usuario, None, solo_no_leidas=True, offset=0, limit=10)
    assert pendientes == 1


async def test_pagina_con_offset_y_limit_y_total_completo(db_session: AsyncSession) -> None:
    repo = SqlAlchemyNotificacionRepository(db_session)
    for clave in ("1", "2", "3"):
        await repo.publicar([_nueva(clave)])
    usuario = await _usuario(db_session)

    items, total = await repo.listar(usuario, None, solo_no_leidas=False, offset=1, limit=1)
    assert total == 3
    assert len(items) == 1
    assert items[0].leida is False
