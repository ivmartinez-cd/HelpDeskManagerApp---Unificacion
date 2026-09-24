"""Tests de integración de SqlAlchemyHistorialEstadosRepository
(`insumos_despacho_estado_historial`)."""

from datetime import date, timedelta

import pytest
from sqlalchemy import func, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    HistorialEstadosRepository,
)
from src.modules.insumos.domain.value_objects.despachados.cambio_estado import CambioEstado
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.infrastructure.models.despacho_estado_historial_model import (
    DespachoEstadoHistorialModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_historial_estados_repository import (  # noqa: E501
    SqlAlchemyHistorialEstadosRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    GUIA,
    OTRA_GUIA,
    crear_envio,
    estado_oca,
)


def _repo(session: AsyncSession) -> HistorialEstadosRepository:
    return SqlAlchemyHistorialEstadosRepository(session)


def _fila_directa(**cambios: object) -> dict[str, object]:
    return {
        "guia": GUIA,
        "id_estado": 5,
        "estado": "En viaje",
        "motivo": "",
        "sucursal": "Rosario",
        "fecha_estado": date(2026, 9, 18),
        "color": "verde",
        **cambios,
    }


async def test_registrar_guarda_el_estado_y_el_color(db_session: AsyncSession) -> None:
    await crear_envio(db_session)
    visita = estado_oca(estado="Visita", id_estado=12, motivo="Domicilio cerrado")

    await _repo(db_session).registrar(GUIA, visita, ColorSemaforo.NARANJA)

    [cambio] = await _repo(db_session).listar_por_guia(GUIA)
    assert cambio == CambioEstado(
        id_estado=12,
        estado="Visita",
        motivo="Domicilio cerrado",
        sucursal="Rosario",
        fecha_estado=date(2026, 9, 18),
        color=ColorSemaforo.NARANJA,
        observado_en=cambio.observado_en,
    )
    assert cambio.observado_en.tzinfo is not None


async def test_acuse_sin_id_estado_motivo_ni_sucursal_se_guarda_con_textos_vacios(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    acuse = estado_oca(estado="Acuse en Rendicion", id_estado=None, sucursal_actual="")

    await _repo(db_session).registrar(GUIA, acuse, ColorSemaforo.CERRADO)

    [cambio] = await _repo(db_session).listar_por_guia(GUIA)
    assert (cambio.id_estado, cambio.motivo, cambio.sucursal) == (None, "", "")


async def test_listar_del_mas_reciente_al_mas_viejo_solo_de_la_guia(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    await crear_envio(db_session, OTRA_GUIA)
    repo = _repo(db_session)
    await repo.registrar(GUIA, estado_oca(estado="En viaje"), ColorSemaforo.VERDE)
    await repo.registrar(GUIA, estado_oca(estado="En sucursal"), ColorSemaforo.ROJO)
    await repo.registrar(OTRA_GUIA, estado_oca(OTRA_GUIA), ColorSemaforo.VERDE)
    # Observado antes que los otros aunque se inserta último (id mayor).
    await db_session.execute(
        insert(DespachoEstadoHistorialModel).values(
            **_fila_directa(estado="Ingresado", observado_en=func.now() - timedelta(days=1))
        )
    )

    cambios = await repo.listar_por_guia(GUIA)

    assert [c.estado for c in cambios] == ["En sucursal", "En viaje", "Ingresado"]


async def test_check_constraint_rechaza_un_color_invalido(db_session: AsyncSession) -> None:
    await crear_envio(db_session)

    with pytest.raises(IntegrityError, match="ck_insumos_despacho_estado_historial_color"):
        await db_session.execute(
            insert(DespachoEstadoHistorialModel).values(**_fila_directa(color="azul"))
        )
