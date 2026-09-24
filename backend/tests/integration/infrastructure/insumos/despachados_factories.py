"""Datos de prueba de Insumos > Despachados para los tests de integración de sus repos."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.insumos.domain.entities.despachados.envio_seguido import (
    CierreAlerta,
    EnvioSeguido,
    ErrorConsulta,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import (
    ClasificacionEnvio,
    ColorSemaforo,
)
from src.modules.insumos.domain.value_objects.despachados.despacho_siges import (
    DespachoSiges,
    IncidenteInsumo,
)
from src.modules.insumos.domain.value_objects.despachados.estado_oca import EstadoOca
from src.modules.insumos.infrastructure.repositories.sqlalchemy_envios_despacho_repository import (  # noqa: E501
    SqlAlchemyEnviosDespachoRepository,
)

GUIA = "3867500000001234567"
OTRA_GUIA = "3867500000007654321"


def momento(dia: int, hora: int = 10, minuto: int = 0) -> datetime:
    """Instante de septiembre de 2026 en UTC (lo que devuelve Postgres en timestamptz)."""
    return datetime(2026, 9, dia, hora, minuto, tzinfo=UTC)


def clasificacion(color: ColorSemaforo = ColorSemaforo.VERDE, **cambios: Any) -> ClasificacionEnvio:
    base = ClasificacionEnvio(
        color=color,
        alerta=False,
        abierto=True,
        fecha_limite=None,
        observacion="",
        estado_desconocido=False,
    )
    return replace(base, **cambios)


def estado_oca(guia: str = GUIA, **cambios: Any) -> EstadoOca:
    base = EstadoOca(
        numero_envio=guia,
        operativa="434324",
        orden_retiro="98765",
        sucursal_actual="Rosario",
        fecha_estado=date(2026, 9, 18),
        estado="En viaje",
        id_estado=5,
        motivo="",
        cantidad_paquetes=1,
    )
    return replace(base, **cambios)


def envio(guia: str = GUIA, **cambios: Any) -> EnvioSeguido:
    base = EnvioSeguido(
        guia=guia,
        id_distribucion=3,
        fecha_remito=date(2026, 9, 15),
        cliente="Cliente SA",
        sucursal_cliente="Casa Central",
        clasificacion=clasificacion(),
    )
    return replace(base, **cambios)


def despacho(id_remito: int, guia: str = GUIA, **cambios: Any) -> DespachoSiges:
    base = DespachoSiges(
        id_remito=id_remito,
        numero_remito=50000 + id_remito,
        guia=guia,
        id_distribucion=3,
        fecha_remito=date(2026, 9, 15),
        bultos=1,
        cliente="Cliente SA",
        sucursal_cliente="Casa Central",
        entrega_a="Recepción",
        incidentes=(IncidenteInsumo(numero="446207", numero_cliente=""),),
    )
    return replace(base, **cambios)


async def crear_envio(session: AsyncSession, guia: str = GUIA) -> EnvioSeguido:
    nuevo = envio(guia)
    await SqlAlchemyEnviosDespachoRepository(session).crear([nuevo])
    return nuevo


async def crear_usuario(session: AsyncSession, nombre: str = "Ana Operadora") -> uuid.UUID:
    usuario = AppUser(
        id=uuid.uuid4(), email=f"{uuid.uuid4()}@test.local", password_hash="x", full_name=nombre
    )
    session.add(usuario)
    await session.flush()
    return usuario.id


async def envio_completo(session: AsyncSession) -> EnvioSeguido:
    """Envío con todos los datos: estado OCA, alerta, error y cierre por un usuario real."""
    usuario_id = await crear_usuario(session, "Ana Operadora")
    return envio(
        clasificacion=clasificacion(
            ColorSemaforo.NARANJA, alerta=True, observacion="Visita fallida"
        ),
        estado_oca=estado_oca(estado="Visita", id_estado=12, motivo="Domicilio cerrado"),
        consultado_en=momento(20, 9, 15),
        ultimo_error=ErrorConsulta(mensaje="Timeout de OCA", ocurrido_en=momento(20, 11)),
        cierre_alerta=CierreAlerta(
            cerrada_en=momento(20, 12), usuario_id=usuario_id, usuario_nombre="Ana Operadora"
        ),
    )


async def borrar_usuario(session: AsyncSession, usuario_id: uuid.UUID) -> None:
    await session.execute(delete(AppUser).where(AppUser.id == usuario_id))
