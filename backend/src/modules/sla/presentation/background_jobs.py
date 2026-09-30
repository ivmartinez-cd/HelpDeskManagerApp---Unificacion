"""Jobs de fondo del módulo sla:

Auto-sync (configurable vía settings):
- sla_refresh: cada 240 min (4 h) — snapshot del período mensual actual contra
  Orion/Siges. Estable dentro del mes; el botón "Actualizar" fuerza uno inmediato.
- pendientes_refresh: cada 60 min (1 h) — backlog de incidentes sin cerrar,
  transversal a períodos; cambia con cada cierre en Gestión, por eso el intervalo
  es más corto.
- aviso_visita_sucursal: cada 15 min — aviso cuando un caso de Mesa de Ayuda
  tiene una visita de técnico en marcha en la misma sucursal (una vez por par):
  en la campanita de la app (función `sla-avisos-mesa-ayuda`) y, si
  `MESA_AYUDA_ALERTA_MAIL_TO` tiene destinatarios, además por mail (SMTP
  general, Mailpit en dev). Solo lee Siges; escribe en
  `sla_avisos_visita_sucursal` y `notificaciones`. Un par registrado cuenta
  como avisado por todos los canales: si el mail se configura después, no se
  mandan por mail los pares que ya estaban en la campanita.

Sin ORION_HOST configurado, los gateways lanzan ExternalServiceError
en cada ciclo — se loguea y se reintenta en el próximo intervalo."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.mailer_factory import get_mailer
from src.modules.notificaciones.infrastructure.repositories.sqlalchemy_notificacion_repository import (  # noqa: E501
    SqlAlchemyNotificacionRepository,
)
from src.modules.sla.application.use_cases.avisar_visitas_en_sucursal_mda import (
    AvisarVisitasEnSucursalMda,
)
from src.modules.sla.application.use_cases.refresh_pendientes_snapshot import (
    RefreshPendientesSnapshot,
)
from src.modules.sla.application.use_cases.refresh_sla_snapshot import RefreshSlaSnapshot
from src.modules.sla.domain.repositories.avisos_visita_sucursal import (
    NotificadorVisitaSucursal,
)
from src.modules.sla.infrastructure.email_aviso_visita_sucursal import (
    EmailNotificadorVisitaSucursal,
)
from src.modules.sla.infrastructure.inapp_aviso_visita_sucursal import (
    InAppNotificadorVisitaSucursal,
    NotificadoresEnSerie,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_pendientes_snapshot_repository import (
    SqlAlchemyPendientesSnapshotRepository,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_prestador_lookup import (
    SqlAlchemyPrestadorLookup,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_registro_avisos_visita import (
    SqlAlchemyRegistroAvisosVisita,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_sla_snapshot_repository import (
    SqlAlchemySlaSnapshotRepository,
)
from src.modules.sla.presentation.dependencies import (
    get_mesa_ayuda_query_gateway,
    get_pendientes_query_gateway,
    get_sla_query_gateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


def _periodo_actual() -> int:
    now = datetime.now(UTC)
    return now.year * 100 + now.month


async def _loop(
    nombre: str, ciclo: Callable[[], Awaitable[None]], interval_minutes: int
) -> None:
    """Corre `ciclo` cada `interval_minutes`; un ciclo fallido se loguea y se
    reintenta en el próximo intervalo, nunca corta el loop."""
    logger.info("%s: iniciando (intervalo %d min)", nombre, interval_minutes)
    while True:
        try:
            await ciclo()
        except Exception as exc:
            logger.error("%s: ciclo fallido", nombre, exc_info=exc)
        await asyncio.sleep(interval_minutes * 60)


async def _ciclo_sla() -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        repo = SqlAlchemySlaSnapshotRepository(session)
        use_case = RefreshSlaSnapshot(get_sla_query_gateway(), repo)
        snapshot = await use_case.execute(_periodo_actual())
        await session.commit()
    logger.info(
        "sla_refresh: OK — periodo=%d total=%d vencidos=%d",
        snapshot.periodo,
        snapshot.total,
        snapshot.vencidos,
    )


async def _ciclo_pendientes() -> None:
    settings = get_settings()
    factory = get_sessionmaker()
    async with factory() as session:
        repo = SqlAlchemyPendientesSnapshotRepository(session)
        use_case = RefreshPendientesSnapshot(
            get_pendientes_query_gateway(),
            repo,
            pst_lookup=SqlAlchemyPrestadorLookup(session),
            meses_corte=settings.pendientes_meses_corte,
        )
        snapshot = await use_case.execute()
        await session.commit()
    logger.info(
        "pendientes_refresh: OK — total=%d por_prestador=%d",
        snapshot.total,
        len(snapshot.por_prestador),
    )


def _notificadores_visita(session: AsyncSession, mail_to: str) -> NotificadoresEnSerie:
    # In-app primero: si el mail falla, la sesión no se confirma y la
    # notificación tampoco queda; el próximo ciclo reintenta los dos.
    notificadores: list[NotificadorVisitaSucursal] = [
        InAppNotificadorVisitaSucursal(SqlAlchemyNotificacionRepository(session))
    ]
    destinatarios = [m.strip() for m in mail_to.split(",") if m.strip()]
    if destinatarios:
        notificadores.append(EmailNotificadorVisitaSucursal(get_mailer(), destinatarios))
    return NotificadoresEnSerie(notificadores)


async def _ciclo_aviso_visita_sucursal() -> None:
    settings = get_settings()
    async with get_sessionmaker()() as session:
        use_case = AvisarVisitasEnSucursalMda(
            get_mesa_ayuda_query_gateway(),
            settings.mesa_ayuda_siges_empresa_id,
            SqlAlchemyRegistroAvisosVisita(session),
            _notificadores_visita(session, settings.mesa_ayuda_alerta_mail_to),
        )
        avisados = await use_case.execute()
        await session.commit()
    logger.info("aviso_visita_sucursal: OK — avisados=%d", avisados)


async def background_sla_refresh_task(interval_minutes: int) -> None:
    await _loop("sla_refresh", _ciclo_sla, interval_minutes)


async def background_pendientes_refresh_task(interval_minutes: int) -> None:
    await _loop("pendientes_refresh", _ciclo_pendientes, interval_minutes)


async def background_aviso_visita_sucursal_task(interval_minutes: int) -> None:
    await _loop("aviso_visita_sucursal", _ciclo_aviso_visita_sucursal, interval_minutes)


def start_sla_background_jobs(interval_minutes: int) -> list[asyncio.Task[None]]:
    settings = get_settings()
    return [
        asyncio.create_task(background_sla_refresh_task(interval_minutes)),
        asyncio.create_task(
            background_pendientes_refresh_task(settings.pendientes_refresh_interval_minutes)
        ),
        asyncio.create_task(
            background_aviso_visita_sucursal_task(settings.mesa_ayuda_alerta_interval_minutes)
        ),
    ]
