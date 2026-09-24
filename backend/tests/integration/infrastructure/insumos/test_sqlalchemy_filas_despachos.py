"""Tests de integración de las columnas de cada fila de SqlAlchemyConsultaDespachosRepository:
primer remito y su primer incidente, cantidades, última acción y todo en una sola sentencia."""

from dataclasses import replace
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import ErrorConsulta
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import IncidenteInsumo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    UltimaAccion,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.integration.infrastructure.insumos.consulta_despachos_datos import (
    AMARILLO,
    NARANJA,
    TODO,
    accion,
    alta,
    con_oca,
    contar_consultas,
    filtros,
    guia_n,
    repo_consulta,
    seguido,
)
from tests.integration.infrastructure.insumos.despachados_factories import despacho, momento


def _inc(numero: str) -> tuple[IncidenteInsumo, ...]:
    return (IncidenteInsumo(numero, ""),)


async def test_fila_con_primer_remito_primer_incidente_y_cantidades(
    db_session: AsyncSession,
) -> None:
    await alta(
        db_session,
        replace(
            con_oca(
                seguido(1, NARANJA, alerta=True, observacion="Visita fallida"),
                estado="Visita",
                motivo="Domicilio cerrado",
                sucursal_actual="Rosario",
            ),
            fecha_remito=date(2026, 9, 12),
            ultimo_error=ErrorConsulta(mensaje="Timeout de OCA", ocurrido_en=momento(20)),
        ),
    )
    await SqlAlchemyRemitosDespachoRepository(db_session).guardar(
        [
            despacho(
                10,
                guia_n(1),
                fecha_remito=date(2026, 9, 14),
                incidentes=(IncidenteInsumo("446207", ""), IncidenteInsumo("446400", "")),
            ),
            despacho(
                20,
                guia_n(1),
                fecha_remito=date(2026, 9, 12),
                incidentes=(IncidenteInsumo("446300", ""), IncidenteInsumo("446207", "OC-1")),
            ),
        ]
    )

    filas = await repo_consulta(db_session).listar(filtros(), TODO)

    assert filas == [
        FilaDespacho(
            guia=guia_n(1),
            color=NARANJA,
            alerta_abierta=True,
            observacion="Visita fallida",
            fecha_limite=None,
            estado="Visita",
            motivo="Domicilio cerrado",
            sucursal_oca="Rosario",
            fecha_estado=date(2026, 9, 18),
            operativa="434324",
            cliente="Cliente SA",
            fecha_remito=date(2026, 9, 12),
            numero_remito=50020,
            cantidad_remitos=2,
            incidente="446207",
            cantidad_incidentes=3,
            ultima_accion=None,
            con_error=True,
        )
    ]


async def test_el_incidente_es_el_primero_del_primer_remito_no_el_menor_de_la_guia(
    db_session: AsyncSession,
) -> None:
    await alta(db_session, seguido(1), seguido(2))
    await SqlAlchemyRemitosDespachoRepository(db_session).guardar(
        [
            despacho(10, guia_n(1), fecha_remito=date(2026, 9, 12), incidentes=_inc("446500")),
            despacho(11, guia_n(1), fecha_remito=date(2026, 9, 14), incidentes=_inc("446100")),
            despacho(20, guia_n(2), fecha_remito=date(2026, 9, 12), incidentes=()),
            despacho(21, guia_n(2), fecha_remito=date(2026, 9, 14), incidentes=_inc("446100")),
        ]
    )

    filas = await repo_consulta(db_session).listar(filtros(), TODO)

    assert {f.guia: (f.numero_remito, f.incidente, f.cantidad_incidentes) for f in filas} == {
        guia_n(1): (50010, "446500", 2),
        guia_n(2): (50020, "", 1),
    }


async def test_fila_sin_oca_ni_remitos_devuelve_textos_vacios(db_session: AsyncSession) -> None:
    await alta(db_session, seguido(1, AMARILLO, fecha_estado=None))

    [fila] = await repo_consulta(db_session).listar(filtros(), TODO)

    assert (fila.estado, fila.motivo, fila.sucursal_oca, fila.operativa) == ("", "", "", "")
    assert (fila.fecha_estado, fila.numero_remito, fila.incidente) == (None, None, "")
    assert (fila.cantidad_remitos, fila.cantidad_incidentes) == (0, 0)
    assert (fila.ultima_accion, fila.con_error, fila.alerta_abierta) == (None, False, False)
    assert fila.dias_habiles_para_limite is None


async def test_ultima_accion_por_fecha_y_despues_por_id(db_session: AsyncSession) -> None:
    await alta(db_session, seguido(1), seguido(2), seguido(3))
    await accion(db_session, guia_n(1), momento(21), tipo="mail_cliente", resultado="resuelto")
    await accion(db_session, guia_n(1), momento(20), tipo="otro")
    await accion(db_session, guia_n(2), momento(20), tipo="llamado_cliente")
    await accion(db_session, guia_n(2), momento(20), usuario_nombre="Beto")

    filas = {
        f.guia: f.ultima_accion for f in await repo_consulta(db_session).listar(filtros(), TODO)
    }

    assert filas == {
        guia_n(1): UltimaAccion(
            TipoAccion.MAIL_CLIENTE, ResultadoAccion.RESUELTO, "Ana", momento(21)
        ),
        guia_n(2): UltimaAccion(
            TipoAccion.RECLAMO_OCA, ResultadoAccion.PENDIENTE, "Beto", momento(20)
        ),
        guia_n(3): None,
    }


async def test_listar_resuelve_todo_en_una_sola_sentencia(db_session: AsyncSession) -> None:
    await alta(db_session, *(seguido(n) for n in range(1, 6)))
    await SqlAlchemyRemitosDespachoRepository(db_session).guardar(
        [
            despacho(n * 10 + k, guia_n(n), incidentes=(IncidenteInsumo(f"44{n}{k}00", ""),))
            for n in range(1, 6)
            for k in (1, 2)
        ]
    )
    for n in range(1, 6):
        await accion(db_session, guia_n(n), momento(20), usuario_nombre=f"Operador {n}")

    with contar_consultas(db_session) as sentencias:
        filas = await repo_consulta(db_session).listar(filtros(), TODO)

    assert len(sentencias) == 1
    assert {
        f.guia: (f.numero_remito, f.incidente, f.cantidad_remitos, f.cantidad_incidentes)
        for f in filas
    } == {guia_n(n): (50000 + n * 10 + 1, f"44{n}100", 2, 2) for n in range(1, 6)}
    assert [f.ultima_accion.usuario_nombre for f in filas if f.ultima_accion] == [
        f"Operador {n}" for n in range(1, 6)
    ]
