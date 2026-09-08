"""Factories del módulo tareas_varias — repositorio y casos de uso.
Separado de `bono_tecnicos` (ver ADR de la separación): las TV siguen
sumando al Puntaje, pero por lectura vía `TareasVariasGateway`
(`bono_tecnicos.infrastructure.tareas_varias`), no porque compartan módulo."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.tareas_varias.application.use_cases.crear_solicitud_tv import CrearSolicitudTv
from src.modules.tareas_varias.application.use_cases.crear_solicitud_tv_admin import (
    CrearSolicitudTvAdmin,
)
from src.modules.tareas_varias.application.use_cases.crear_solicitud_tv_propia import (
    CrearSolicitudTvPropia,
)
from src.modules.tareas_varias.application.use_cases.decidir_solicitud_tv import (
    DecidirSolicitudTv,
)
from src.modules.tareas_varias.application.use_cases.listar_solicitudes_tv import (
    ListarSolicitudesTv,
)
from src.modules.tareas_varias.application.use_cases.listar_solicitudes_tv_propias import (
    ListarSolicitudesTvPropias,
)
from src.modules.tareas_varias.infrastructure.repositories.sqlalchemy_solicitud_tv_repository import (  # noqa: E501
    SqlAlchemySolicitudTvRepository,
)
from src.modules.tareas_varias.infrastructure.vacaciones.sqlalchemy_tecnico_identity_gateway import (  # noqa: E501
    SqlAlchemyTecnicoIdentityGateway,
)


def build_crear_solicitud_tv(session: AsyncSession) -> CrearSolicitudTv:
    return CrearSolicitudTv(SqlAlchemySolicitudTvRepository(session))


def build_crear_solicitud_tv_propia(session: AsyncSession) -> CrearSolicitudTvPropia:
    return CrearSolicitudTvPropia(
        SqlAlchemyTecnicoIdentityGateway(session), build_crear_solicitud_tv(session)
    )


def build_crear_solicitud_tv_admin(session: AsyncSession) -> CrearSolicitudTvAdmin:
    return CrearSolicitudTvAdmin(SqlAlchemySolicitudTvRepository(session))


def build_listar_solicitudes_tv(session: AsyncSession) -> ListarSolicitudesTv:
    return ListarSolicitudesTv(SqlAlchemySolicitudTvRepository(session))


def build_listar_solicitudes_tv_propias(session: AsyncSession) -> ListarSolicitudesTvPropias:
    return ListarSolicitudesTvPropias(
        SqlAlchemyTecnicoIdentityGateway(session), SqlAlchemySolicitudTvRepository(session)
    )


def build_decidir_solicitud_tv(session: AsyncSession) -> DecidirSolicitudTv:
    return DecidirSolicitudTv(SqlAlchemySolicitudTvRepository(session))
