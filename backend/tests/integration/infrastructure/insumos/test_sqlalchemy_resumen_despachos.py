"""Tests de integración de las tarjetas y contadores del menú de Despachados
(`SqlAlchemyConsultaDespachosRepository.resumir`)."""

from dataclasses import replace
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    ResumenDespachos,
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
    accion,
    alta,
    con_oca,
    contar_consultas,
    guia_n,
    repo_consulta,
    seguido,
)
from tests.integration.infrastructure.insumos.despachados_factories import momento


async def test_resumir_cuenta_por_color_alertas_y_operativas(db_session: AsyncSession) -> None:
    await alta(
        db_session,
        seguido(1, ROJO, alerta=True, fecha_limite=date(2026, 9, 25)),
        replace(
            seguido(2, ROJO, alerta=True, fecha_limite=date(2026, 9, 22)), cierre_alerta=CIERRE
        ),
        seguido(3, NARANJA, alerta=True),
        replace(seguido(4, NARANJA, alerta=True), cierre_alerta=CIERRE),
        seguido(5, NARANJA, alerta=True),
        con_oca(seguido(6, AMARILLO), operativa="443913"),
        con_oca(seguido(7), operativa=""),
        seguido(8, fecha_estado=None),
        replace(
            con_oca(seguido(9, CERRADO, abierto=False), operativa="999999"),
            fecha_remito=date(2026, 8, 1),
        ),
        con_oca(seguido(10, CERRADO, abierto=False), operativa="434305"),
    )
    await accion(db_session, guia_n(4), momento(20))
    await accion(db_session, guia_n(5), momento(20))

    with contar_consultas(db_session) as sentencias:
        resumen = await repo_consulta(db_session).resumir(ALCANCE)

    assert resumen == ResumenDespachos(
        por_color={ROJO: 2, NARANJA: 3, AMARILLO: 1, VERDE: 2, GRIS: 0, CERRADO: 1},
        alertas_rojas=1,
        alertas_naranjas=2,
        naranjas_sin_accion=1,
        limite_mas_proximo=date(2026, 9, 22),
        operativas=("434305", "434324", "443913"),
    )
    assert list(resumen.por_color) == list(ColorSemaforo)
    assert len(sentencias) == 2


async def test_resumir_sin_envios(db_session: AsyncSession) -> None:
    resumen = await repo_consulta(db_session).resumir(ALCANCE)

    assert resumen == ResumenDespachos(
        por_color=dict.fromkeys(ColorSemaforo, 0),
        alertas_rojas=0,
        alertas_naranjas=0,
        naranjas_sin_accion=0,
        limite_mas_proximo=None,
        operativas=(),
    )
