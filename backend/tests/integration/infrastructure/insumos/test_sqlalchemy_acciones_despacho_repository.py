"""Tests de integración de SqlAlchemyAccionesDespachoRepository (`insumos_despacho_accion`)."""

from dataclasses import asdict, replace
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import func, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    AccionRegistrada,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.repositories.acciones_despacho_repository import (
    AccionesDespachoRepository,
)
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_acciones_despacho_repository import (  # noqa: E501
    SqlAlchemyAccionesDespachoRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    GUIA,
    OTRA_GUIA,
    borrar_usuario,
    crear_envio,
    crear_usuario,
)


def _repo(session: AsyncSession) -> AccionesDespachoRepository:
    return SqlAlchemyAccionesDespachoRepository(session)


def _accion(**cambios: Any) -> AccionNueva:
    base = AccionNueva(
        guia=GUIA,
        tipo=TipoAccion.LLAMADO_CLIENTE,
        detalle="Se llamó al cliente: retira mañana por sucursal.",
        resultado=ResultadoAccion.RESUELTO,
        cerro_alerta=True,
        usuario_id=None,
        usuario_nombre="Ana Operadora",
    )
    return replace(base, **cambios)


async def test_agregar_devuelve_la_accion_con_id_y_fecha_de_la_base(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    nueva = _accion(usuario_id=await crear_usuario(db_session))

    registrada = await _repo(db_session).agregar(nueva)

    assert registrada == AccionRegistrada(
        id=registrada.id, creada_en=registrada.creada_en, **asdict(nueva)
    )
    assert registrada.creada_en.tzinfo is not None
    assert await _repo(db_session).listar_por_guia(GUIA) == [registrada]


async def test_listar_de_la_mas_reciente_a_la_mas_vieja_solo_de_la_guia(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    await crear_envio(db_session, OTRA_GUIA)
    repo = _repo(db_session)
    primera = await repo.agregar(_accion(tipo=TipoAccion.MAIL_CLIENTE))
    segunda = await repo.agregar(_accion(tipo=TipoAccion.RECLAMO_OCA, cerro_alerta=False))
    await repo.agregar(_accion(guia=OTRA_GUIA))
    # Creada antes que las otras aunque se inserta última (id mayor).
    await db_session.execute(
        insert(DespachoAccionModel).values(
            guia=GUIA,
            tipo="otro",
            detalle="Carga retroactiva",
            resultado="sin_respuesta",
            usuario_nombre="Ana Operadora",
            creada_en=func.now() - timedelta(days=1),
        )
    )

    acciones = await repo.listar_por_guia(GUIA)

    assert [a.id for a in acciones[:2]] == [segunda.id, primera.id]
    assert (acciones[2].tipo, acciones[2].cerro_alerta) == (TipoAccion.OTRO, False)


async def test_baja_del_usuario_deja_la_accion_con_su_nombre(db_session: AsyncSession) -> None:
    await crear_envio(db_session)
    usuario_id = await crear_usuario(db_session)
    registrada = await _repo(db_session).agregar(_accion(usuario_id=usuario_id))

    await borrar_usuario(db_session, usuario_id)

    assert await _repo(db_session).listar_por_guia(GUIA) == [replace(registrada, usuario_id=None)]


@pytest.mark.parametrize(
    ("columna", "valor", "restriccion"),
    [
        ("tipo", "visita", "ck_insumos_despacho_accion_tipo"),
        ("resultado", "quizas", "ck_insumos_despacho_accion_resultado"),
    ],
)
async def test_check_constraints_rechazan_tipo_o_resultado_invalido(
    db_session: AsyncSession, columna: str, valor: str, restriccion: str
) -> None:
    await crear_envio(db_session)
    fila = {
        "guia": GUIA,
        "tipo": "otro",
        "detalle": "x",
        "resultado": "pendiente",
        "usuario_nombre": "Ana",
        columna: valor,
    }

    with pytest.raises(IntegrityError, match=restriccion):
        await db_session.execute(insert(DespachoAccionModel).values(**fila))
