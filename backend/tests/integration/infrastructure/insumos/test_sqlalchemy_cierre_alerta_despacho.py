"""Tests de integración de `SqlAlchemyEnviosDespachoRepository.registrar_cierre_alerta`: el
cierre de un operador escribe solo sus columnas y no pisa lo que el job guardó entretanto."""

from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.envio_seguido import CierreAlerta
from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    EnviosDespachoRepository,
)
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_envios_despacho_repository import (  # noqa: E501
    SqlAlchemyEnviosDespachoRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    GUIA,
    OTRA_GUIA,
    crear_usuario,
    envio,
    envio_completo,
    momento,
)


def _repo(session: AsyncSession) -> EnviosDespachoRepository:
    return SqlAlchemyEnviosDespachoRepository(session)


async def _cierre_de_ana(session: AsyncSession) -> CierreAlerta:
    usuario_id = await crear_usuario(session, "Ana Operadora")
    return CierreAlerta(
        cerrada_en=momento(21, 9), usuario_id=usuario_id, usuario_nombre="Ana Operadora"
    )


async def test_no_pisa_el_estado_que_el_job_guardo_despues_de_la_lectura(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    await repo.crear([envio(GUIA)])
    assert await repo.obtener(GUIA) == envio(GUIA)  # lo que leyó el request del operador
    del_job = replace(await envio_completo(db_session), cierre_alerta=None)
    await repo.actualizar(del_job)  # el job guarda otro estado de OCA entretanto
    cierre = await _cierre_de_ana(db_session)

    await repo.registrar_cierre_alerta(GUIA, cierre)

    assert await repo.obtener(GUIA) == replace(del_job, cierre_alerta=cierre)


async def test_solo_toca_la_guia_indicada_y_marca_la_hora_real(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    await repo.crear([envio(GUIA), envio(OTRA_GUIA)])
    cierre = await _cierre_de_ana(db_session)

    await repo.registrar_cierre_alerta(GUIA, cierre)

    assert await repo.obtener(GUIA) == envio(GUIA, cierre_alerta=cierre)
    assert await repo.obtener(OTRA_GUIA) == envio(OTRA_GUIA)
    filas = await db_session.execute(
        select(
            DespachoEnvioModel.guia,
            DespachoEnvioModel.creado_en,
            DespachoEnvioModel.actualizado_en,
        )
    )
    marcadas = {guia: actualizado_en > creado_en for guia, creado_en, actualizado_en in filas}
    assert marcadas == {GUIA: True, OTRA_GUIA: False}


async def test_una_guia_sin_envio_no_hace_nada(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    cierre = await _cierre_de_ana(db_session)

    await repo.registrar_cierre_alerta(GUIA, cierre)

    assert await repo.obtener(GUIA) is None
