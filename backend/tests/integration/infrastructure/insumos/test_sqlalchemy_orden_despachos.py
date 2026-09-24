"""Tests de integración del orden por columna del listado de SqlAlchemyConsultaDespachosRepository:
cada columna en las dos direcciones, los vacíos siempre al final y la guía como desempate. El
orden por urgencia (el defecto) está en `test_sqlalchemy_consulta_despachos_repository.py`."""

from dataclasses import replace
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import IncidenteInsumo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    ColumnaOrden,
    OrdenDespachos,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.integration.infrastructure.insumos.consulta_despachos_datos import (
    NARANJA,
    ROJO,
    VERDE,
    alta,
    con_oca,
    guia_n,
    guias_listadas,
    seguido,
)
from tests.integration.infrastructure.insumos.despachados_factories import despacho


async def _alta_para_ordenar(session: AsyncSession) -> None:
    """Cuatro envíos con valores distintos por columna. El 3 no tiene estado OCA, remito ni
    incidente; el 2 no tiene límite; el 4 no tiene incidente y empata con el 2 en cliente
    (sin distinguir mayúsculas) y fecha de remito, y con el 3 en color."""
    envios = [
        _envio(1, seguido(1, ROJO, fecha_limite=date(2026, 9, 25)), "Beta", 12),
        _envio(2, seguido(2, NARANJA), "Alfa", 14),
        _envio(
            3, seguido(3, VERDE, fecha_estado=None, fecha_limite=date(2026, 9, 22)), "Gamma", 10
        ),
        _envio(4, seguido(4, VERDE, fecha_limite=date(2026, 9, 28)), "ALFA", 14),
    ]
    oca = {
        1: {"estado": "Entregado", "sucursal_actual": "Rosario", "fecha_estado": date(2026, 9, 18)},
        2: {"estado": "Arribo", "sucursal_actual": "Mendoza", "fecha_estado": date(2026, 9, 10)},
        4: {"estado": "Visita", "sucursal_actual": "Salta", "fecha_estado": date(2026, 9, 20)},
    }
    await alta(session, *(con_oca(e, **oca[n]) if n in oca else e for n, e in envios))
    await SqlAlchemyRemitosDespachoRepository(session).guardar(
        [
            despacho(11, guia_n(1), numero_remito=300, incidentes=(IncidenteInsumo("446300", ""),)),
            despacho(12, guia_n(2), numero_remito=100, incidentes=(IncidenteInsumo("446100", ""),)),
            despacho(14, guia_n(4), numero_remito=200, incidentes=()),
        ]
    )


def _envio(n: int, base: EnvioSeguido, cliente: str, dia_remito: int) -> tuple[int, EnvioSeguido]:
    return n, replace(base, cliente=cliente, fecha_remito=date(2026, 9, dia_remito))


@pytest.mark.parametrize(
    ("columna", "ascendente", "descendente"),
    [
        (ColumnaOrden.COLOR, [1, 2, 3, 4], [3, 4, 2, 1]),
        (ColumnaOrden.GUIA, [1, 2, 3, 4], [4, 3, 2, 1]),
        (ColumnaOrden.REMITO, [2, 4, 1, 3], [1, 4, 2, 3]),
        (ColumnaOrden.CLIENTE, [2, 4, 1, 3], [3, 1, 2, 4]),
        (ColumnaOrden.INCIDENTE, [2, 1, 3, 4], [1, 2, 3, 4]),
        (ColumnaOrden.ESTADO, [2, 1, 4, 3], [4, 1, 2, 3]),
        (ColumnaOrden.SUCURSAL, [2, 1, 4, 3], [4, 1, 2, 3]),
        (ColumnaOrden.FECHA_REMITO, [3, 1, 2, 4], [2, 4, 1, 3]),
        (ColumnaOrden.FECHA_ESTADO, [2, 1, 4, 3], [4, 1, 2, 3]),
        (ColumnaOrden.LIMITE, [3, 1, 4, 2], [4, 1, 3, 2]),
    ],
)
async def test_ordena_por_columna_con_vacios_al_final_y_desempate_por_guia(
    db_session: AsyncSession,
    columna: ColumnaOrden,
    ascendente: list[int],
    descendente: list[int],
) -> None:
    await _alta_para_ordenar(db_session)

    asc = await guias_listadas(db_session, orden=OrdenDespachos(columna, descendente=False))
    desc = await guias_listadas(db_session, orden=OrdenDespachos(columna, descendente=True))

    assert asc == [guia_n(n) for n in ascendente]
    assert desc == [guia_n(n) for n in descendente]


async def test_estado_vacio_de_oca_va_al_final_como_si_no_hubiera(
    db_session: AsyncSession,
) -> None:
    await alta(
        db_session,
        con_oca(seguido(1), estado=""),
        con_oca(seguido(2), estado="Visita"),
        con_oca(seguido(3), estado="Arribo"),
    )

    for descendente in (False, True):
        orden = OrdenDespachos(ColumnaOrden.ESTADO, descendente)
        assert (await guias_listadas(db_session, orden=orden))[-1] == guia_n(1)


async def test_urgencia_ignora_la_direccion(db_session: AsyncSession) -> None:
    await _alta_para_ordenar(db_session)

    asc = await guias_listadas(db_session, orden=OrdenDespachos(ColumnaOrden.URGENCIA, False))
    desc = await guias_listadas(db_session, orden=OrdenDespachos(ColumnaOrden.URGENCIA, True))

    assert asc == desc == await guias_listadas(db_session)
    assert asc[0] == guia_n(1)
