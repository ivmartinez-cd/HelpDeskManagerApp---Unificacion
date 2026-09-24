"""Tests de integración de SqlAlchemyConsultaDespachosRepository: orden por urgencia,
filtros, alcance, columnas de cada fila (sin N+1) y resumen de tarjetas."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
    ErrorConsulta,
)
from src.modules.insumos.domain.repositories.consulta_despachos_repository import (
    ConsultaDespachosRepository,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import IncidenteInsumo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    FiltrosDespachos,
    Pagina,
    ResumenDespachos,
    UltimaAccion,
)
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_consulta_despachos_repository import (  # noqa: E501
    SqlAlchemyConsultaDespachosRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_envios_despacho_repository import (  # noqa: E501
    SqlAlchemyEnviosDespachoRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_remitos_despacho_repository import (  # noqa: E501
    SqlAlchemyRemitosDespachoRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    clasificacion,
    despacho,
    envio,
    estado_oca,
    momento,
)

ROJO, NARANJA, AMARILLO = ColorSemaforo.ROJO, ColorSemaforo.NARANJA, ColorSemaforo.AMARILLO
VERDE, GRIS, CERRADO = ColorSemaforo.VERDE, ColorSemaforo.GRIS, ColorSemaforo.CERRADO
ALCANCE = date(2026, 9, 1)
TODO = Pagina(limite=100, desplazamiento=0)
CIERRE = CierreAlerta(cerrada_en=momento(20), usuario_id=None, usuario_nombre="Ana")


def _guia(n: int) -> str:
    return f"{n:019d}"


def _seguido(
    n: int,
    color: ColorSemaforo = VERDE,
    fecha_estado: date | None = date(2026, 9, 18),
    **clasif: Any,
) -> EnvioSeguido:
    """Envío `n` abierto del color pedido; sin estado OCA si `fecha_estado` es None."""
    estado = None if fecha_estado is None else estado_oca(_guia(n), fecha_estado=fecha_estado)
    return envio(_guia(n), clasificacion=clasificacion(color, **clasif), estado_oca=estado)


def _con_oca(seguido: EnvioSeguido, **cambios: Any) -> EnvioSeguido:
    return replace(seguido, estado_oca=estado_oca(seguido.guia, **cambios))


def _filtros(**cambios: Any) -> FiltrosDespachos:
    return FiltrosDespachos(alcance_desde=ALCANCE, **cambios)


def _repo(session: AsyncSession) -> ConsultaDespachosRepository:
    return SqlAlchemyConsultaDespachosRepository(session)


async def _alta(session: AsyncSession, *envios: EnvioSeguido) -> None:
    await SqlAlchemyEnviosDespachoRepository(session).crear(list(envios))


async def _accion(session: AsyncSession, guia: str, creada_en: datetime, **cambios: Any) -> None:
    datos = {"tipo": "reclamo_oca", "resultado": "pendiente", "usuario_nombre": "Ana"} | cambios
    session.add(DespachoAccionModel(guia=guia, detalle="x", creada_en=creada_en, **datos))
    await session.flush()


async def _guias(session: AsyncSession, **filtros: Any) -> list[str]:
    """Guías listadas con esos filtros; de paso verifica que `contar` coincida."""
    criterio = _filtros(**filtros)
    filas = await _repo(session).listar(criterio, TODO)
    assert await _repo(session).contar(criterio) == len(filas)
    return [fila.guia for fila in filas]


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


async def _alta_todos_los_colores(session: AsyncSession) -> list[str]:
    """Da de alta envíos de todos los colores (en orden inverso) y devuelve las guías en el
    orden de urgencia esperado."""
    envios = [
        _seguido(1, ROJO, fecha_limite=date(2026, 9, 25)),
        _seguido(2, ROJO, fecha_limite=date(2026, 9, 22)),
        _seguido(3, ROJO, fecha_limite=date(2026, 9, 22)),
        _seguido(4, NARANJA, fecha_estado=date(2026, 9, 18)),
        _seguido(5, NARANJA, fecha_estado=date(2026, 9, 10)),
        _seguido(6, AMARILLO, fecha_estado=None),
        _seguido(7, AMARILLO, fecha_estado=date(2026, 9, 12)),
        _seguido(8, VERDE, fecha_estado=date(2026, 9, 10)),
        _seguido(9, VERDE, fecha_estado=None),
        _seguido(10, VERDE, fecha_estado=date(2026, 9, 20)),
        _seguido(11, GRIS, fecha_estado=date(2026, 9, 5)),
        _seguido(12, CERRADO, fecha_estado=date(2026, 9, 19), abierto=False),
        _seguido(13, CERRADO, fecha_estado=date(2026, 9, 21), abierto=False),
    ]
    await _alta(session, *reversed(envios))
    return [_guia(n) for n in (2, 3, 1, 5, 4, 7, 6, 10, 8, 9, 11, 13, 12)]


async def test_listar_ordena_por_urgencia_con_sus_desempates(db_session: AsyncSession) -> None:
    esperado = await _alta_todos_los_colores(db_session)

    assert await _guias(db_session) == esperado


async def test_listar_pagina_sobre_el_orden_de_urgencia(db_session: AsyncSession) -> None:
    esperado = await _alta_todos_los_colores(db_session)

    filas = await _repo(db_session).listar(_filtros(), Pagina(limite=3, desplazamiento=2))

    assert [f.guia for f in filas] == esperado[2:5]
    assert await _repo(db_session).contar(_filtros()) == 13


async def test_filtra_por_colores(db_session: AsyncSession) -> None:
    await _alta(db_session, _seguido(1, VERDE), _seguido(2, GRIS), _seguido(3, ROJO))

    assert await _guias(db_session, colores=(GRIS, ROJO)) == [_guia(3), _guia(2)]


async def test_filtra_por_operativa(db_session: AsyncSession) -> None:
    await _alta(
        db_session,
        _con_oca(_seguido(1), operativa="434305"),
        _con_oca(_seguido(2), operativa="434324"),
        _seguido(3, fecha_estado=None),
    )

    assert await _guias(db_session, operativa="434305") == [_guia(1)]
    assert len(await _guias(db_session, operativa="")) == 3


async def test_filtra_por_fecha_de_remito_inclusive(db_session: AsyncSession) -> None:
    await _alta(
        db_session,
        *(replace(_seguido(dia), fecha_remito=date(2026, 9, dia)) for dia in (9, 10, 12, 13)),
    )

    desde_hasta = await _guias(
        db_session, remito_desde=date(2026, 9, 10), remito_hasta=date(2026, 9, 12)
    )

    assert sorted(desde_hasta) == [_guia(10), _guia(12)]
    assert sorted(await _guias(db_session, remito_desde=date(2026, 9, 12))) == [
        _guia(12),
        _guia(13),
    ]
    assert await _guias(db_session, remito_hasta=date(2026, 9, 9)) == [_guia(9)]


async def test_solo_alertas_abiertas_excluye_las_cerradas_y_las_sin_alerta(
    db_session: AsyncSession,
) -> None:
    await _alta(
        db_session,
        _seguido(1, ROJO, alerta=True, fecha_limite=date(2026, 9, 25)),
        replace(_seguido(2, NARANJA, alerta=True), cierre_alerta=CIERRE),
        _seguido(3, NARANJA, alerta=True),
        _seguido(4, VERDE),
    )

    assert await _guias(db_session, solo_alertas_abiertas=True) == [_guia(1), _guia(3)]


async def _alta_para_busqueda(session: AsyncSession) -> None:
    await _alta(
        session,
        replace(_seguido(1), guia="3867512345678901234", cliente="Toner 100% SA"),
        replace(_seguido(2), cliente="toner 1000 sa"),
        replace(_seguido(3), cliente="Insumos_Norte"),
        replace(_seguido(4), cliente="InsumosXNorte"),
        replace(_seguido(5), cliente="Otro"),
    )
    incidentes = (IncidenteInsumo("446207", "OC-55"), IncidenteInsumo("446300", ""))
    await SqlAlchemyRemitosDespachoRepository(session).guardar(
        [despacho(7, _guia(5), numero_remito=777123, incidentes=incidentes)]
    )


async def test_texto_busca_en_guia_cliente_remito_e_incidente(db_session: AsyncSession) -> None:
    await _alta_para_busqueda(db_session)

    assert await _guias(db_session, texto="56789") == ["3867512345678901234"]
    assert sorted(await _guias(db_session, texto=" TONER ")) == [
        _guia(2),
        "3867512345678901234",
    ]
    assert await _guias(db_session, texto="7771") == [_guia(5)]
    assert await _guias(db_session, texto="446300") == [_guia(5)]
    assert await _guias(db_session, texto="oc-55") == [_guia(5)]


async def test_texto_escapa_los_comodines_de_like(db_session: AsyncSession) -> None:
    await _alta_para_busqueda(db_session)

    assert await _guias(db_session, texto="100%") == ["3867512345678901234"]
    assert await _guias(db_session, texto="s_n") == [_guia(3)]


async def test_texto_vacio_o_en_blanco_no_filtra(db_session: AsyncSession) -> None:
    await _alta_para_busqueda(db_session)

    assert len(await _guias(db_session, texto="")) == 5
    assert len(await _guias(db_session, texto="   ")) == 5


async def test_alcance_deja_los_abiertos_viejos_y_saca_los_cerrados_viejos(
    db_session: AsyncSession,
) -> None:
    await _alta(
        db_session,
        replace(_seguido(1, CERRADO, abierto=False), fecha_remito=date(2026, 8, 31)),
        replace(_seguido(2, VERDE), fecha_remito=date(2026, 8, 1)),
        replace(_seguido(3, CERRADO, abierto=False), fecha_remito=ALCANCE),
    )

    assert await _guias(db_session) == [_guia(2), _guia(3)]


async def test_fila_con_primer_remito_primer_incidente_y_cantidades(
    db_session: AsyncSession,
) -> None:
    await _alta(
        db_session,
        replace(
            _con_oca(
                _seguido(1, NARANJA, alerta=True, observacion="Visita fallida"),
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
                _guia(1),
                fecha_remito=date(2026, 9, 14),
                incidentes=(IncidenteInsumo("446207", ""), IncidenteInsumo("446400", "")),
            ),
            despacho(
                20,
                _guia(1),
                fecha_remito=date(2026, 9, 12),
                incidentes=(IncidenteInsumo("446300", ""), IncidenteInsumo("446207", "OC-1")),
            ),
        ]
    )

    filas = await _repo(db_session).listar(_filtros(), TODO)

    assert filas == [
        FilaDespacho(
            guia=_guia(1),
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


async def test_fila_sin_oca_ni_remitos_devuelve_textos_vacios(db_session: AsyncSession) -> None:
    await _alta(db_session, _seguido(1, AMARILLO, fecha_estado=None))

    [fila] = await _repo(db_session).listar(_filtros(), TODO)

    assert (fila.estado, fila.motivo, fila.sucursal_oca, fila.operativa) == ("", "", "", "")
    assert (fila.fecha_estado, fila.numero_remito, fila.incidente) == (None, None, "")
    assert (fila.cantidad_remitos, fila.cantidad_incidentes) == (0, 0)
    assert (fila.ultima_accion, fila.con_error, fila.alerta_abierta) == (None, False, False)
    assert fila.dias_habiles_para_limite is None


async def test_ultima_accion_por_fecha_y_despues_por_id(db_session: AsyncSession) -> None:
    await _alta(db_session, _seguido(1), _seguido(2), _seguido(3))
    await _accion(db_session, _guia(1), momento(21), tipo="mail_cliente", resultado="resuelto")
    await _accion(db_session, _guia(1), momento(20), tipo="otro")
    await _accion(db_session, _guia(2), momento(20), tipo="llamado_cliente")
    await _accion(db_session, _guia(2), momento(20), usuario_nombre="Beto")

    filas = {f.guia: f.ultima_accion for f in await _repo(db_session).listar(_filtros(), TODO)}

    assert filas == {
        _guia(1): UltimaAccion(
            TipoAccion.MAIL_CLIENTE, ResultadoAccion.RESUELTO, "Ana", momento(21)
        ),
        _guia(2): UltimaAccion(
            TipoAccion.RECLAMO_OCA, ResultadoAccion.PENDIENTE, "Beto", momento(20)
        ),
        _guia(3): None,
    }


async def test_listar_resuelve_todo_en_una_sola_sentencia(db_session: AsyncSession) -> None:
    await _alta(db_session, *(_seguido(n) for n in range(1, 6)))
    await SqlAlchemyRemitosDespachoRepository(db_session).guardar(
        [
            despacho(n * 10 + k, _guia(n), incidentes=(IncidenteInsumo(f"44{n}{k}00", ""),))
            for n in range(1, 6)
            for k in (1, 2)
        ]
    )
    for n in range(1, 6):
        await _accion(db_session, _guia(n), momento(20), usuario_nombre=f"Operador {n}")

    with _contar_consultas(db_session) as sentencias:
        filas = await _repo(db_session).listar(_filtros(), TODO)

    assert len(sentencias) == 1
    assert {
        f.guia: (f.numero_remito, f.incidente, f.cantidad_remitos, f.cantidad_incidentes)
        for f in filas
    } == {_guia(n): (50000 + n * 10 + 1, f"44{n}100", 2, 2) for n in range(1, 6)}
    assert [f.ultima_accion.usuario_nombre for f in filas if f.ultima_accion] == [
        f"Operador {n}" for n in range(1, 6)
    ]


async def test_resumir_cuenta_por_color_alertas_y_operativas(db_session: AsyncSession) -> None:
    await _alta(
        db_session,
        _seguido(1, ROJO, alerta=True, fecha_limite=date(2026, 9, 25)),
        replace(
            _seguido(2, ROJO, alerta=True, fecha_limite=date(2026, 9, 22)), cierre_alerta=CIERRE
        ),
        _seguido(3, NARANJA, alerta=True),
        replace(_seguido(4, NARANJA, alerta=True), cierre_alerta=CIERRE),
        _seguido(5, NARANJA, alerta=True),
        _con_oca(_seguido(6, AMARILLO), operativa="443913"),
        _con_oca(_seguido(7), operativa=""),
        _seguido(8, fecha_estado=None),
        replace(
            _con_oca(_seguido(9, CERRADO, abierto=False), operativa="999999"),
            fecha_remito=date(2026, 8, 1),
        ),
        _con_oca(_seguido(10, CERRADO, abierto=False), operativa="434305"),
    )
    await _accion(db_session, _guia(4), momento(20))
    await _accion(db_session, _guia(5), momento(20))

    with _contar_consultas(db_session) as sentencias:
        resumen = await _repo(db_session).resumir(ALCANCE)

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
    resumen = await _repo(db_session).resumir(ALCANCE)

    assert resumen == ResumenDespachos(
        por_color=dict.fromkeys(ColorSemaforo, 0),
        alertas_rojas=0,
        alertas_naranjas=0,
        naranjas_sin_accion=0,
        limite_mas_proximo=None,
        operativas=(),
    )
