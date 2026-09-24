"""Tests de integración del listado de SqlAlchemyConsultaDespachosRepository: orden por
urgencia, paginado, filtros, búsqueda de texto y alcance. Las columnas de cada fila están en
`test_sqlalchemy_filas_despachos.py` y las tarjetas en `test_sqlalchemy_resumen_despachos.py`."""

from dataclasses import replace
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.despachados.despacho_siges import IncidenteInsumo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import Pagina
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.integration.infrastructure.insumos.consulta_despachos_datos import (
    ALCANCE,
    AMARILLO,
    CERRADO,
    CIERRE,
    GRIS,
    NARANJA,
    ROJO,
    VERDE,
    alta,
    con_oca,
    filtros,
    guia_n,
    guias_listadas,
    repo_consulta,
    seguido,
)
from tests.integration.infrastructure.insumos.despachados_factories import despacho


async def _alta_todos_los_colores(session: AsyncSession) -> list[str]:
    """Da de alta envíos de todos los colores (en orden inverso) y devuelve las guías en el
    orden de urgencia esperado."""
    envios = [
        seguido(1, ROJO, fecha_limite=date(2026, 9, 25)),
        seguido(2, ROJO, fecha_limite=date(2026, 9, 22)),
        seguido(3, ROJO, fecha_limite=date(2026, 9, 22)),
        seguido(4, NARANJA, fecha_estado=date(2026, 9, 18)),
        seguido(5, NARANJA, fecha_estado=date(2026, 9, 10)),
        seguido(6, AMARILLO, fecha_estado=None),
        seguido(7, AMARILLO, fecha_estado=date(2026, 9, 12)),
        seguido(8, VERDE, fecha_estado=date(2026, 9, 10)),
        seguido(9, VERDE, fecha_estado=None),
        seguido(10, VERDE, fecha_estado=date(2026, 9, 20)),
        seguido(11, GRIS, fecha_estado=date(2026, 9, 5)),
        seguido(12, CERRADO, fecha_estado=date(2026, 9, 19), abierto=False),
        seguido(13, CERRADO, fecha_estado=date(2026, 9, 21), abierto=False),
    ]
    await alta(session, *reversed(envios))
    return [guia_n(n) for n in (2, 3, 1, 5, 4, 7, 6, 10, 8, 9, 11, 13, 12)]


async def test_listar_ordena_por_urgencia_con_sus_desempates(db_session: AsyncSession) -> None:
    esperado = await _alta_todos_los_colores(db_session)

    assert await guias_listadas(db_session) == esperado


async def test_listar_pagina_sobre_el_orden_de_urgencia(db_session: AsyncSession) -> None:
    esperado = await _alta_todos_los_colores(db_session)

    filas = await repo_consulta(db_session).listar(filtros(), Pagina(limite=3, desplazamiento=2))

    assert [f.guia for f in filas] == esperado[2:5]
    assert await repo_consulta(db_session).contar(filtros()) == 13


async def test_filtra_por_colores(db_session: AsyncSession) -> None:
    await alta(db_session, seguido(1, VERDE), seguido(2, GRIS), seguido(3, ROJO))

    assert await guias_listadas(db_session, colores=(GRIS, ROJO)) == [guia_n(3), guia_n(2)]


async def test_filtra_por_operativa(db_session: AsyncSession) -> None:
    await alta(
        db_session,
        con_oca(seguido(1), operativa="434305"),
        con_oca(seguido(2), operativa="434324"),
        seguido(3, fecha_estado=None),
    )

    assert await guias_listadas(db_session, operativa="434305") == [guia_n(1)]
    assert len(await guias_listadas(db_session, operativa="")) == 3


async def test_filtra_por_fecha_de_remito_inclusive(db_session: AsyncSession) -> None:
    await alta(
        db_session,
        *(replace(seguido(dia), fecha_remito=date(2026, 9, dia)) for dia in (9, 10, 12, 13)),
    )

    desde_hasta = await guias_listadas(
        db_session, remito_desde=date(2026, 9, 10), remito_hasta=date(2026, 9, 12)
    )

    assert sorted(desde_hasta) == [guia_n(10), guia_n(12)]
    assert sorted(await guias_listadas(db_session, remito_desde=date(2026, 9, 12))) == [
        guia_n(12),
        guia_n(13),
    ]
    assert await guias_listadas(db_session, remito_hasta=date(2026, 9, 9)) == [guia_n(9)]


async def test_solo_alertas_abiertas_excluye_las_cerradas_y_las_sin_alerta(
    db_session: AsyncSession,
) -> None:
    await alta(
        db_session,
        seguido(1, ROJO, alerta=True, fecha_limite=date(2026, 9, 25)),
        replace(seguido(2, NARANJA, alerta=True), cierre_alerta=CIERRE),
        seguido(3, NARANJA, alerta=True),
        seguido(4, VERDE),
    )

    assert await guias_listadas(db_session, solo_alertas_abiertas=True) == [guia_n(1), guia_n(3)]


async def _alta_para_busqueda(session: AsyncSession) -> None:
    await alta(
        session,
        replace(seguido(1), guia="3867512345678901234", cliente="Toner 100% SA"),
        replace(seguido(2), cliente="toner 1000 sa"),
        replace(seguido(3), cliente="Insumos_Norte"),
        replace(seguido(4), cliente="InsumosXNorte"),
        replace(seguido(5), cliente="Otro"),
    )
    incidentes = (IncidenteInsumo("446207", "OC-55"), IncidenteInsumo("446300", ""))
    await SqlAlchemyRemitosDespachoRepository(session).guardar(
        [despacho(7, guia_n(5), numero_remito=777123, incidentes=incidentes)]
    )


async def test_texto_busca_en_guia_cliente_remito_e_incidente(db_session: AsyncSession) -> None:
    await _alta_para_busqueda(db_session)

    assert await guias_listadas(db_session, texto="56789") == ["3867512345678901234"]
    assert sorted(await guias_listadas(db_session, texto=" TONER ")) == [
        guia_n(2),
        "3867512345678901234",
    ]
    assert await guias_listadas(db_session, texto="7771") == [guia_n(5)]
    assert await guias_listadas(db_session, texto="446300") == [guia_n(5)]
    assert await guias_listadas(db_session, texto="oc-55") == [guia_n(5)]


async def test_texto_no_distingue_tildes_ni_mayusculas(db_session: AsyncSession) -> None:
    await alta(
        db_session,
        replace(seguido(1), cliente="Metalúrgica Córdoba SA"),
        replace(seguido(2), cliente="ÑANDÚ INSUMOS"),
        replace(seguido(3), cliente="Otro"),
    )
    incidentes = (IncidenteInsumo("446207", "Pedido Ñuñoa"),)
    await SqlAlchemyRemitosDespachoRepository(db_session).guardar(
        [despacho(7, guia_n(3), incidentes=incidentes)]
    )

    assert await guias_listadas(db_session, texto="metalurgica") == [guia_n(1)]
    assert await guias_listadas(db_session, texto="CORDOBA") == [guia_n(1)]
    assert await guias_listadas(db_session, texto="Córdoba") == [guia_n(1)]
    assert await guias_listadas(db_session, texto="nandu") == [guia_n(2)]
    assert await guias_listadas(db_session, texto="ñuñoa") == [guia_n(3)]


async def test_texto_escapa_los_comodines_de_like(db_session: AsyncSession) -> None:
    await _alta_para_busqueda(db_session)

    assert await guias_listadas(db_session, texto="100%") == ["3867512345678901234"]
    assert await guias_listadas(db_session, texto="s_n") == [guia_n(3)]


async def test_texto_vacio_o_en_blanco_no_filtra(db_session: AsyncSession) -> None:
    await _alta_para_busqueda(db_session)

    assert len(await guias_listadas(db_session, texto="")) == 5
    assert len(await guias_listadas(db_session, texto="   ")) == 5


async def test_alcance_deja_los_abiertos_viejos_y_saca_los_cerrados_viejos(
    db_session: AsyncSession,
) -> None:
    await alta(
        db_session,
        replace(seguido(1, CERRADO, abierto=False), fecha_remito=date(2026, 8, 31)),
        replace(seguido(2, VERDE), fecha_remito=date(2026, 8, 1)),
        replace(seguido(3, CERRADO, abierto=False), fecha_remito=ALCANCE),
    )

    assert await guias_listadas(db_session) == [guia_n(2), guia_n(3)]
