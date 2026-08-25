"""Factories del módulo bono_tecnicos — gateway, repositorio y casos de uso.
Singleton de proceso (`lru_cache`) para el gateway, como el resto de los
módulos que consultan Mercurio. El chequeo de host y el runner con su
semáforo viven en `require_mercurio_runner` (ADR-018)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv import CrearSolicitudTv
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv_admin import (
    CrearSolicitudTvAdmin,
)
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv_propia import (
    CrearSolicitudTvPropia,
)
from src.modules.bono_tecnicos.application.use_cases.decidir_solicitud_tv import (
    DecidirSolicitudTv,
)
from src.modules.bono_tecnicos.application.use_cases.get_incidentes_tecnico import (
    GetIncidentesTecnico,
)
from src.modules.bono_tecnicos.application.use_cases.get_puntajes_periodo import (
    GetPuntajesPeriodo,
)
from src.modules.bono_tecnicos.application.use_cases.guardar_bono_input import GuardarBonoInput
from src.modules.bono_tecnicos.application.use_cases.listar_solicitudes_tv import (
    ListarSolicitudesTv,
)
from src.modules.bono_tecnicos.application.use_cases.listar_solicitudes_tv_propias import (
    ListarSolicitudesTvPropias,
)
from src.modules.bono_tecnicos.infrastructure.mercurio.pyodbc_conteo_tecnico_gateway import (
    PyodbcConteoTecnicoGateway,
)
from src.modules.bono_tecnicos.infrastructure.repositories.sqlalchemy_bono_tecnico_input_repository import (  # noqa: E501
    SqlAlchemyBonoTecnicoInputRepository,
)
from src.modules.bono_tecnicos.infrastructure.repositories.sqlalchemy_solicitud_tv_repository import (  # noqa: E501
    SqlAlchemySolicitudTvRepository,
)
from src.modules.bono_tecnicos.infrastructure.vacaciones.sqlalchemy_dias_sugeridos_gateway import (  # noqa: E501
    SqlAlchemyDiasSugeridosGateway,
)
from src.modules.bono_tecnicos.infrastructure.vacaciones.sqlalchemy_tecnico_identity_gateway import (  # noqa: E501
    SqlAlchemyTecnicoIdentityGateway,
)
from src.shared.infrastructure.mercurio.factories import require_mercurio_runner


@lru_cache
def get_conteo_tecnico_gateway() -> PyodbcConteoTecnicoGateway:
    return PyodbcConteoTecnicoGateway(require_mercurio_runner())


def build_get_puntajes_periodo(session: AsyncSession) -> GetPuntajesPeriodo:
    return GetPuntajesPeriodo(
        get_conteo_tecnico_gateway(),
        SqlAlchemyBonoTecnicoInputRepository(session),
        SqlAlchemyDiasSugeridosGateway(session),
        SqlAlchemySolicitudTvRepository(session),
    )


def build_guardar_bono_input(session: AsyncSession) -> GuardarBonoInput:
    return GuardarBonoInput(SqlAlchemyBonoTecnicoInputRepository(session))


def build_get_incidentes_tecnico() -> GetIncidentesTecnico:
    return GetIncidentesTecnico(get_conteo_tecnico_gateway())


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
