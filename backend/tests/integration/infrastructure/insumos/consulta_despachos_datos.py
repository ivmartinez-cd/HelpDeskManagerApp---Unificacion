"""Datos y ayudas compartidos por los tests de integración de
SqlAlchemyConsultaDespachosRepository (listado, filas y resumen)."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
)
from src.modules.insumos.domain.repositories.consulta_despachos_repository import (
    ConsultaDespachosRepository,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FiltrosDespachos,
    Pagina,
)
from src.modules.insumos.infrastructure.models.despacho_accion_model import DespachoAccionModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_consulta_despachos_repository import (  # noqa: E501
    SqlAlchemyConsultaDespachosRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_envios_despacho_repository import (  # noqa: E501
    SqlAlchemyEnviosDespachoRepository,
)
from tests.integration.infrastructure.insumos.despachados_factories import (
    clasificacion,
    envio,
    estado_oca,
    momento,
)

ROJO, NARANJA, AMARILLO = ColorSemaforo.ROJO, ColorSemaforo.NARANJA, ColorSemaforo.AMARILLO
VERDE, GRIS, CERRADO = ColorSemaforo.VERDE, ColorSemaforo.GRIS, ColorSemaforo.CERRADO
ALCANCE = date(2026, 9, 1)
TODO = Pagina(limite=100, desplazamiento=0)
CIERRE = CierreAlerta(cerrada_en=momento(20), usuario_id=None, usuario_nombre="Ana")


def guia_n(n: int) -> str:
    return f"{n:019d}"


def seguido(
    n: int,
    color: ColorSemaforo = VERDE,
    fecha_estado: date | None = date(2026, 9, 18),
    **clasif: Any,
) -> EnvioSeguido:
    """Envío `n` abierto del color pedido; sin estado OCA si `fecha_estado` es None."""
    estado = None if fecha_estado is None else estado_oca(guia_n(n), fecha_estado=fecha_estado)
    return envio(guia_n(n), clasificacion=clasificacion(color, **clasif), estado_oca=estado)


def con_oca(original: EnvioSeguido, **cambios: Any) -> EnvioSeguido:
    return replace(original, estado_oca=estado_oca(original.guia, **cambios))


def filtros(**cambios: Any) -> FiltrosDespachos:
    return FiltrosDespachos(alcance_desde=ALCANCE, **cambios)


def repo_consulta(session: AsyncSession) -> ConsultaDespachosRepository:
    return SqlAlchemyConsultaDespachosRepository(session)


async def alta(session: AsyncSession, *envios: EnvioSeguido) -> None:
    await SqlAlchemyEnviosDespachoRepository(session).crear(list(envios))


async def accion(session: AsyncSession, guia: str, creada_en: datetime, **cambios: Any) -> None:
    datos = {"tipo": "reclamo_oca", "resultado": "pendiente", "usuario_nombre": "Ana"} | cambios
    session.add(DespachoAccionModel(guia=guia, detalle="x", creada_en=creada_en, **datos))
    await session.flush()


async def guias_listadas(session: AsyncSession, **cambios: Any) -> list[str]:
    """Guías listadas con esos filtros; de paso verifica que `contar` coincida."""
    criterio = filtros(**cambios)
    filas = await repo_consulta(session).listar(criterio, TODO)
    assert await repo_consulta(session).contar(criterio) == len(filas)
    return [fila.guia for fila in filas]


@contextmanager
def contar_consultas(session: AsyncSession) -> Iterator[list[str]]:
    """Anota cada sentencia que la sesión manda a la base mientras dura el bloque."""
    sentencias: list[str] = []

    def _anotar(*args: Any) -> None:
        sentencias.append(args[2])

    motor = session.bind.engine.sync_engine
    event.listen(motor, "before_cursor_execute", _anotar)
    try:
        yield sentencias
    finally:
        event.remove(motor, "before_cursor_execute", _anotar)
