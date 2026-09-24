"""Tests de integración de SqlAlchemyEnviosDespachoRepository (`insumos_despacho_envio`)."""

from dataclasses import replace
from datetime import date
from typing import cast

import pytest
from sqlalchemy import delete, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionNueva,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import CierreAlerta
from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    EnviosDespachoRepository,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel
from src.modules.insumos.infrastructure.models.despacho_estado_historial_model import (
    DespachoEstadoHistorialModel,
)
from src.modules.insumos.infrastructure.models.despacho_remito_model import (
    DespachoIncidenteModel,
    DespachoRemitoModel,
)
from src.modules.insumos.infrastructure.repositories.mapeo_envio_despacho import columnas_alta
from src.modules.insumos.infrastructure.repositories.sqlalchemy_acciones_despacho_repository import (  # noqa: E501
    SqlAlchemyAccionesDespachoRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_envios_despacho_repository import (  # noqa: E501
    SqlAlchemyEnviosDespachoRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_historial_estados_repository import (  # noqa: E501
    SqlAlchemyHistorialEstadosRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    GUIA,
    OTRA_GUIA,
    borrar_usuario,
    clasificacion,
    despacho,
    envio,
    envio_completo,
    estado_oca,
    momento,
)


def _repo(session: AsyncSession) -> EnviosDespachoRepository:
    return SqlAlchemyEnviosDespachoRepository(session)


def _sin_base() -> AsyncSession:
    """Sesión que falla ante cualquier uso: prueba que el repo no consulta."""
    return cast(AsyncSession, object())


async def test_ida_y_vuelta_de_un_envio_completo(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    completo = await envio_completo(db_session)

    await repo.crear([completo])

    assert await repo.obtener(GUIA) == completo


async def test_ida_y_vuelta_sin_estado_oca_error_ni_cierre(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    esperando = envio(
        clasificacion=clasificacion(ColorSemaforo.GRIS, observacion="Esperando ingreso en OCA")
    )

    await repo.crear([esperando])

    guardado = await repo.obtener(GUIA)
    assert guardado == esperando
    assert guardado is not None and guardado.estado_oca is None


async def test_ida_y_vuelta_de_un_acuse_sin_id_estado(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    acuse = envio(
        clasificacion=clasificacion(ColorSemaforo.CERRADO, abierto=False),
        estado_oca=estado_oca(estado="Acuse en Rendicion", id_estado=None, cantidad_paquetes=None),
        consultado_en=momento(21),
    )

    await repo.crear([acuse])

    assert await repo.obtener(GUIA) == acuse


async def test_ida_y_vuelta_de_rojo_con_fecha_limite_y_cierre_sin_usuario(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    rojo = envio(
        clasificacion=clasificacion(
            ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 25)
        ),
        estado_oca=estado_oca(estado="En sucursal", id_estado=7, sucursal_actual="Córdoba"),
        cierre_alerta=CierreAlerta(
            cerrada_en=momento(22), usuario_id=None, usuario_nombre="Usuario dado de baja"
        ),
    )

    await repo.crear([rojo])

    assert await repo.obtener(GUIA) == rojo


async def test_obtener_guia_inexistente_devuelve_none(db_session: AsyncSession) -> None:
    assert await _repo(db_session).obtener(GUIA) is None


async def test_guias_seguidas_devuelve_solo_las_que_existen(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    await repo.crear([envio(GUIA), envio(OTRA_GUIA)])

    seguidas = await repo.guias_seguidas({GUIA, OTRA_GUIA, "3867500000000000000"})

    assert seguidas == {GUIA, OTRA_GUIA}


async def test_con_listas_vacias_no_consulta_la_base() -> None:
    repo = _repo(_sin_base())

    assert await repo.guias_seguidas([]) == set()
    await repo.crear([])


async def test_crear_ignora_una_guia_existente_sin_pisarla(db_session: AsyncSession) -> None:
    repo = _repo(db_session)
    original = envio(GUIA, cliente="Cliente Original")
    await repo.crear([original])

    await repo.crear([envio(GUIA, cliente="Otro Cliente"), envio(OTRA_GUIA)])

    assert await repo.obtener(GUIA) == original
    assert await repo.obtener(OTRA_GUIA) == envio(OTRA_GUIA)


async def test_actualizar_persiste_el_seguimiento_sin_tocar_datos_de_siges(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    original = envio()
    await repo.crear([original])
    assert await repo.listar_abiertos() == [original]  # como en el job: listar y actualizar
    completo = await envio_completo(db_session)
    cambiado_en_siges = replace(
        completo,
        id_distribucion=10,
        fecha_remito=date(2026, 9, 1),
        cliente="Otro Cliente",
        sucursal_cliente="Otra Sucursal",
    )

    await repo.actualizar(cambiado_en_siges)

    assert await repo.obtener(GUIA) == replace(
        completo,
        id_distribucion=original.id_distribucion,
        fecha_remito=original.fecha_remito,
        cliente=original.cliente,
        sucursal_cliente=original.sucursal_cliente,
    )


async def test_actualizar_sin_estado_oca_vacia_columnas_oca_error_y_cierre(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    completo = await envio_completo(db_session)
    await repo.crear([completo])
    assert await repo.obtener(GUIA) == completo  # queda cargado en la sesión antes del UPDATE
    sin_datos = envio(clasificacion=clasificacion(ColorSemaforo.GRIS, observacion="Sin datos"))

    await repo.actualizar(sin_datos)

    assert await repo.obtener(GUIA) == sin_datos
    oca = (
        await db_session.execute(
            select(DespachoEnvioModel.oca_estado, DespachoEnvioModel.oca_id_estado)
        )
    ).one()
    assert tuple(oca) == (None, None)


async def test_actualizar_solo_toca_la_guia_indicada_y_marca_la_hora_real(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    await repo.crear([envio(GUIA), envio(OTRA_GUIA)])
    completo = await envio_completo(db_session)

    await repo.actualizar(completo)

    assert await repo.obtener(GUIA) == completo
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


async def test_listar_abiertos_excluye_cerrados_y_ordena_por_fecha_y_guia(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    cerrado = clasificacion(ColorSemaforo.CERRADO, abierto=False)
    await repo.crear(
        [
            envio("3867500000000000003", fecha_remito=date(2026, 9, 10)),
            envio("3867500000000000002", fecha_remito=date(2026, 9, 8)),
            envio("3867500000000000001", fecha_remito=date(2026, 9, 10)),
            envio("3867500000000000000", fecha_remito=date(2026, 9, 1), clasificacion=cerrado),
        ]
    )

    abiertos = await repo.listar_abiertos()

    assert [e.guia for e in abiertos] == [
        "3867500000000000002",
        "3867500000000000001",
        "3867500000000000003",
    ]


async def test_baja_del_usuario_del_cierre_deja_el_nombre_aunque_la_sesion_retenga_la_fila(
    db_session: AsyncSession,
) -> None:
    repo = _repo(db_session)
    completo = await envio_completo(db_session)
    await repo.crear([completo])
    assert completo.cierre_alerta is not None and completo.cierre_alerta.usuario_id is not None
    # Modelo vivo en el identity map, como si algo lo retuviera: las lecturas releen la base.
    _retenida = (await db_session.execute(select(DespachoEnvioModel))).scalar_one()

    await borrar_usuario(db_session, completo.cierre_alerta.usuario_id)  # ON DELETE SET NULL

    sin_usuario = replace(completo, cierre_alerta=replace(completo.cierre_alerta, usuario_id=None))
    assert await repo.obtener(GUIA) == sin_usuario
    assert await repo.listar_abiertos() == [sin_usuario]


async def test_check_constraint_rechaza_un_color_invalido(db_session: AsyncSession) -> None:
    fila = {**columnas_alta(envio()), "color": "violeta"}

    with pytest.raises(IntegrityError, match="ck_insumos_despacho_envio_color"):
        await db_session.execute(insert(DespachoEnvioModel).values(**fila))


async def test_borrar_el_envio_borra_en_cascada_lo_que_cuelga_de_la_guia(
    db_session: AsyncSession,
) -> None:
    await _repo(db_session).crear([envio()])
    await SqlAlchemyRemitosDespachoRepository(db_session).guardar([despacho(10)])
    await SqlAlchemyHistorialEstadosRepository(db_session).registrar(
        GUIA, estado_oca(), ColorSemaforo.VERDE
    )
    await SqlAlchemyAccionesDespachoRepository(db_session).agregar(
        AccionNueva(GUIA, TipoAccion.OTRO, "Nota", ResultadoAccion.PENDIENTE, False, None, "Ana")
    )

    await db_session.execute(delete(DespachoEnvioModel).where(DespachoEnvioModel.guia == GUIA))

    for modelo in (
        DespachoRemitoModel,
        DespachoIncidenteModel,
        DespachoEstadoHistorialModel,
        DespachoAccionModel,
    ):
        total = await db_session.scalar(select(func.count()).select_from(modelo))
        assert total == 0, modelo.__tablename__
