"""Tests de integración de SqlAlchemyRemitosDespachoRepository (`insumos_despacho_remito`
e `insumos_despacho_incidente`)."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from typing import Any, cast

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.repositories.envios_despacho_repository import (
    RemitosDespachoRepository,
)
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import IncidenteInsumo
from src.modules.insumos.infrastructure.models.despacho_remito_model import (
    DespachoIncidenteModel,
    DespachoRemitoModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    GUIA,
    OTRA_GUIA,
    crear_envio,
    despacho,
)


def _repo(session: AsyncSession) -> RemitosDespachoRepository:
    return SqlAlchemyRemitosDespachoRepository(session)


def _incidente(numero: str, numero_cliente: str = "") -> IncidenteInsumo:
    return IncidenteInsumo(numero=numero, numero_cliente=numero_cliente)


@contextmanager
def _contar_consultas(session: AsyncSession) -> Iterator[list[str]]:
    sentencias: list[str] = []

    def _anotar(*args: Any) -> None:
        sentencias.append(args[2])

    motor = session.bind.engine.sync_engine
    event.listen(motor, "before_cursor_execute", _anotar)
    try:
        yield sentencias
    finally:
        event.remove(motor, "before_cursor_execute", _anotar)


async def test_guardar_y_listar_un_remito_con_dos_incidentes(db_session: AsyncSession) -> None:
    await crear_envio(db_session)
    remito = despacho(10, incidentes=(_incidente("446300", "OC-9"), _incidente("446207")))

    await _repo(db_session).guardar([remito])

    listados = await _repo(db_session).listar_por_guia(GUIA)
    assert listados == [
        despacho(10, incidentes=(_incidente("446207"), _incidente("446300", "OC-9")))
    ]


async def test_guia_con_varios_remitos_ordenados_por_fecha_y_id(db_session: AsyncSession) -> None:
    await crear_envio(db_session)
    await crear_envio(db_session, OTRA_GUIA)
    await _repo(db_session).guardar(
        [
            despacho(20, fecha_remito=date(2026, 9, 12)),
            despacho(30, fecha_remito=date(2026, 9, 10)),
            despacho(10, fecha_remito=date(2026, 9, 12)),
            despacho(40, OTRA_GUIA),
        ]
    )

    listados = await _repo(db_session).listar_por_guia(GUIA)

    assert [r.id_remito for r in listados] == [30, 10, 20]


async def test_remito_sin_incidentes_y_guia_sin_remitos(db_session: AsyncSession) -> None:
    await crear_envio(db_session)
    await crear_envio(db_session, OTRA_GUIA)

    await _repo(db_session).guardar([despacho(10, incidentes=())])

    assert await _repo(db_session).listar_por_guia(GUIA) == [despacho(10, incidentes=())]
    assert await _repo(db_session).listar_por_guia(OTRA_GUIA) == []


async def test_guardar_de_nuevo_actualiza_el_remito_y_suma_incidentes_sin_duplicar(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    await _repo(db_session).guardar([despacho(10, incidentes=(_incidente("446207"),))])
    corregido = despacho(
        10,
        numero_remito=77777,
        fecha_remito=date(2026, 9, 16),
        bultos=3,
        id_distribucion=10,
        cliente="Cliente Nuevo SA",
        sucursal_cliente="Sucursal Norte",
        entrega_a="Depósito",
        incidentes=(_incidente("446207", "OC-1"), _incidente("446208")),
    )

    await _repo(db_session).guardar([corregido])

    assert await _repo(db_session).listar_por_guia(GUIA) == [corregido]
    total = await db_session.scalar(select(func.count()).select_from(DespachoIncidenteModel))
    assert total == 2


async def test_guardar_tolera_un_remito_repetido_en_el_mismo_lote(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    ultimo = despacho(10, bultos=5)

    await _repo(db_session).guardar([despacho(10, bultos=1), ultimo])

    assert await _repo(db_session).listar_por_guia(GUIA) == [ultimo]


async def test_guia_corregida_en_siges_mueve_el_remito_a_la_guia_nueva(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    await crear_envio(db_session, OTRA_GUIA)
    await _repo(db_session).guardar([despacho(10)])

    await _repo(db_session).guardar([despacho(10, guia=OTRA_GUIA)])

    assert await _repo(db_session).listar_por_guia(GUIA) == []
    assert await _repo(db_session).listar_por_guia(OTRA_GUIA) == [despacho(10, guia=OTRA_GUIA)]


async def test_listar_hace_una_consulta_de_remitos_y_una_de_incidentes(
    db_session: AsyncSession,
) -> None:
    await crear_envio(db_session)
    await _repo(db_session).guardar(
        [despacho(n, incidentes=(_incidente(f"44620{n}"),)) for n in range(1, 6)]
    )

    with _contar_consultas(db_session) as sentencias:
        listados = await _repo(db_session).listar_por_guia(GUIA)

    assert len(listados) == 5
    assert len(sentencias) == 2


async def test_guardar_lista_vacia_no_consulta_la_base() -> None:
    await _repo(cast(AsyncSession, object())).guardar([])


async def test_guardar_un_remito_de_una_guia_sin_envio_viola_la_fk(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(IntegrityError):
        await _repo(db_session).guardar([despacho(10)])


async def test_guardar_escribe_en_lote_una_sentencia_por_tabla(db_session: AsyncSession) -> None:
    await crear_envio(db_session)
    remitos = [despacho(n, incidentes=(_incidente("1"), _incidente("2"))) for n in range(1, 30)]

    with _contar_consultas(db_session) as sentencias:
        await _repo(db_session).guardar(remitos)

    assert len(sentencias) == 2
    total = await db_session.scalar(select(func.count()).select_from(DespachoRemitoModel))
    assert total == 29
