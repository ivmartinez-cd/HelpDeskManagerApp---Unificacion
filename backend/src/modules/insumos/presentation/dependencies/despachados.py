"""Factories de Insumos > Despachados: un `build_*` por caso de uso a partir de una
`AsyncSession`, más los singletons de proceso (gateways de Siges y OCA, candado).

El gateway de OCA es singleton para reusar su cliente httpx (pool de conexiones); el de
Siges envuelve el runner de ORION compartido. `require_orion_runner` lanza
`ExternalServiceError` si falta ORION_HOST: se resuelve recién al armar la sincronización,
así las pantallas (que leen solo la base de HDM) funcionan igual.
"""

import asyncio
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.dtos.despachados import ConfigConsulta
from src.modules.insumos.application.use_cases.despachados.acciones_despacho import (
    AccionDespachoPorts,
    CerrarAlertaDespacho,
    RegistrarAccionDespacho,
)
from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ConsultaDespachosPorts,
    ConsultarActualizacion,
    ListarDespachos,
    ObtenerDetalleDespacho,
    ResumirDespachos,
)
from src.modules.insumos.application.use_cases.despachados.reclamo_oca import PrepararReclamoOca
from src.modules.insumos.application.use_cases.despachados.sincronizar_despachos import (
    ConfigSincronizacion,
    SincronizarDespachos,
    SincronizarDespachosPorts,
)
from src.modules.insumos.domain.value_objects.despachados.reclamo_oca import (
    ContactoReclamoOca,
    ReglaContactoReclamo,
)
from src.modules.insumos.infrastructure.oca.httpx_oca_seguimiento_gateway import (
    HttpxOcaSeguimientoGateway,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_acciones_despacho_repository import (  # noqa: E501
    SqlAlchemyAccionesDespachoRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_consulta_despachos_repository import (  # noqa: E501
    SqlAlchemyConsultaDespachosRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_corridas_despacho_repository import (  # noqa: E501
    SqlAlchemyCorridasDespachoRepository,
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
from src.modules.insumos.infrastructure.siges.pyodbc_despachos_siges_gateway import (
    PyodbcDespachosSigesGateway,
)
from src.modules.insumos.infrastructure.vacaciones.sqlalchemy_calendario_feriados import (
    SqlAlchemyCalendarioFeriados,
)
from src.modules.insumos.presentation.wiring import app_timezone
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.engine import get_engine
from src.shared.infrastructure.locks.postgres_advisory_lock import (
    INSUMOS_DESPACHADOS_SINCRONIZAR_LOCK_KEY,
    PostgresAdvisoryLock,
)
from src.shared.infrastructure.orion.factories import require_orion_runner


def ahora_utc() -> datetime:
    """Reloj de los casos de uso de Despachados: hora actual, aware en UTC."""
    return datetime.now(UTC)


@lru_cache
def get_despachos_siges_gateway() -> PyodbcDespachosSigesGateway:
    """Singleton sobre el runner de ORION compartido (ADR-018/ADR-039)."""
    return PyodbcDespachosSigesGateway(require_orion_runner())


@lru_cache
def get_oca_seguimiento_gateway() -> HttpxOcaSeguimientoGateway:
    """Singleton: un solo cliente httpx por proceso para todas las corridas."""
    settings = get_settings()
    return HttpxOcaSeguimientoGateway(settings.oca_url_estado_actual, settings.oca_timeout_segundos)


@lru_cache
def get_despachados_lock() -> PostgresAdvisoryLock:
    """Candado que comparten el job programado y "Actualizar ahora"."""
    return PostgresAdvisoryLock(get_engine(), INSUMOS_DESPACHADOS_SINCRONIZAR_LOCK_KEY)


def config_consulta() -> ConfigConsulta:
    """Ventana de la vista y zona horaria del "hoy", desde settings."""
    return ConfigConsulta(
        dias_ventana=get_settings().despachados_dias_ventana, zona_horaria=app_timezone()
    )


def config_sincronizacion() -> ConfigSincronizacion:
    """Parámetros de una corrida del job, desde settings."""
    settings = get_settings()
    return ConfigSincronizacion(
        dias_ventana=settings.despachados_dias_ventana,
        distribuciones=settings.despachados_distribuciones_oca,
        dias_sin_movimiento=settings.despachados_dias_sin_movimiento,
        pausa_segundos=settings.oca_pausa_segundos,
        zona_horaria=app_timezone(),
    )


def _consulta_ports(session: AsyncSession) -> ConsultaDespachosPorts:
    """Puertos de lectura de la pantalla, todos sobre la sesión del request."""
    return ConsultaDespachosPorts(
        consulta=SqlAlchemyConsultaDespachosRepository(session),
        envios=SqlAlchemyEnviosDespachoRepository(session),
        remitos=SqlAlchemyRemitosDespachoRepository(session),
        historial=SqlAlchemyHistorialEstadosRepository(session),
        acciones=SqlAlchemyAccionesDespachoRepository(session),
        corridas=SqlAlchemyCorridasDespachoRepository(session),
        feriados=SqlAlchemyCalendarioFeriados(session),
        reloj=ahora_utc,
    )


def _accion_ports(session: AsyncSession) -> AccionDespachoPorts:
    """Puertos de las acciones de operador (escriben en la transacción del request)."""
    return AccionDespachoPorts(
        envios=SqlAlchemyEnviosDespachoRepository(session),
        acciones=SqlAlchemyAccionesDespachoRepository(session),
        reloj=ahora_utc,
    )


def build_listar_despachos(session: AsyncSession) -> ListarDespachos:
    """Tabla de envíos (y bandeja "Requieren acción")."""
    return ListarDespachos(_consulta_ports(session), config_consulta())


def build_resumir_despachos(session: AsyncSession) -> ResumirDespachos:
    """Tarjetas y contadores."""
    return ResumirDespachos(_consulta_ports(session), config_consulta())


def build_obtener_detalle_despacho(session: AsyncSession) -> ObtenerDetalleDespacho:
    """Detalle de una guía."""
    return ObtenerDetalleDespacho(_consulta_ports(session), config_consulta())


def build_consultar_actualizacion(session: AsyncSession) -> ConsultarActualizacion:
    """Estado de la última corrida."""
    return ConsultarActualizacion(_consulta_ports(session))


def reglas_contacto_reclamo() -> tuple[ReglaContactoReclamo, ...]:
    """Contactos de "Reclamar en OCA" por prefijo de guía, desde settings."""
    return tuple(
        ReglaContactoReclamo(
            prefijo=c.prefijo,
            cuenta=c.cuenta,
            contacto=ContactoReclamoOca(
                nombre=c.nombre,
                apellido=c.apellido,
                empresa=c.empresa,
                email=c.email,
                cuit=c.cuit,
                telefono=c.telefono,
            ),
        )
        for c in get_settings().oca_reclamo_contactos
    )


def build_preparar_reclamo_oca(session: AsyncSession) -> PrepararReclamoOca:
    """Datos para el formulario de reclamos de OCA de una guía."""
    detalle = ObtenerDetalleDespacho(_consulta_ports(session), config_consulta())
    return PrepararReclamoOca(detalle, reglas_contacto_reclamo())


def build_registrar_accion_despacho(session: AsyncSession) -> RegistrarAccionDespacho:
    """Registrar una acción de operador sobre una guía."""
    return RegistrarAccionDespacho(_accion_ports(session))


def build_cerrar_alerta_despacho(session: AsyncSession) -> CerrarAlertaDespacho:
    """Dar por atendida la alerta de una guía."""
    return CerrarAlertaDespacho(_accion_ports(session))


def build_sincronizar_despachos(session: AsyncSession) -> SincronizarDespachos:
    """Una corrida del job; confirma y revierte sobre `session` (propia de la corrida)."""
    ports = SincronizarDespachosPorts(
        siges=get_despachos_siges_gateway(),
        oca=get_oca_seguimiento_gateway(),
        envios=SqlAlchemyEnviosDespachoRepository(session),
        remitos=SqlAlchemyRemitosDespachoRepository(session),
        historial=SqlAlchemyHistorialEstadosRepository(session),
        corridas=SqlAlchemyCorridasDespachoRepository(session),
        feriados=SqlAlchemyCalendarioFeriados(session),
        candado=get_despachados_lock(),
        confirmar=session.commit,
        revertir=session.rollback,
        reloj=ahora_utc,
        pausar=asyncio.sleep,
    )
    return SincronizarDespachos(ports, config_sincronizacion())
