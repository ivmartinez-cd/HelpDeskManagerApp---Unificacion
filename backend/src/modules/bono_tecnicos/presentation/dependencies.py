"""Factories del módulo bono_tecnicos — gateway, repositorio y casos de uso.
Singleton de proceso (`lru_cache`) para el gateway, como el resto de los
módulos que consultan Orion. El chequeo de host y el runner con su
semáforo viven en `require_orion_runner` (ADR-018)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.application.use_cases.get_evolucion_anual import (
    GetEvolucionAnual,
    GetEvolucionAnualPorts,
)
from src.modules.bono_tecnicos.application.use_cases.get_incidentes_tecnico import (
    GetIncidentesTecnico,
)
from src.modules.bono_tecnicos.application.use_cases.get_mi_resumen_bono import GetMiResumenBono
from src.modules.bono_tecnicos.application.use_cases.get_puntajes_periodo import (
    GetPuntajesPeriodo,
)
from src.modules.bono_tecnicos.application.use_cases.get_vinculo_siges import GetVinculoSiges
from src.modules.bono_tecnicos.application.use_cases.guardar_bono_input import GuardarBonoInput
from src.modules.bono_tecnicos.infrastructure.orion.pyodbc_conteo_tecnico_gateway import (
    PyodbcConteoTecnicoGateway,
)
from src.modules.bono_tecnicos.infrastructure.repositories.sqlalchemy_bono_tecnico_input_repository import (  # noqa: E501
    SqlAlchemyBonoTecnicoInputRepository,
)
from src.modules.bono_tecnicos.infrastructure.tareas_varias.sqlalchemy_tareas_varias_gateway import (  # noqa: E501
    SqlAlchemyTareasVariasGateway,
)
from src.modules.bono_tecnicos.infrastructure.vacaciones.sqlalchemy_dias_sugeridos_gateway import (  # noqa: E501
    SqlAlchemyDiasSugeridosGateway,
)
from src.modules.bono_tecnicos.infrastructure.vacaciones.sqlalchemy_tecnico_identity_gateway import (  # noqa: E501
    SqlAlchemyTecnicoIdentityGateway,
)
from src.shared.infrastructure.orion.factories import require_orion_runner


@lru_cache
def get_conteo_tecnico_gateway() -> PyodbcConteoTecnicoGateway:
    return PyodbcConteoTecnicoGateway(require_orion_runner())


def build_get_puntajes_periodo(session: AsyncSession) -> GetPuntajesPeriodo:
    return GetPuntajesPeriodo(
        get_conteo_tecnico_gateway(),
        SqlAlchemyBonoTecnicoInputRepository(session),
        SqlAlchemyDiasSugeridosGateway(session),
        SqlAlchemyTareasVariasGateway(session),
    )


def build_guardar_bono_input(session: AsyncSession) -> GuardarBonoInput:
    return GuardarBonoInput(SqlAlchemyBonoTecnicoInputRepository(session))


def build_get_incidentes_tecnico() -> GetIncidentesTecnico:
    return GetIncidentesTecnico(get_conteo_tecnico_gateway())


def build_get_evolucion_anual(session: AsyncSession) -> GetEvolucionAnual:
    return GetEvolucionAnual(
        GetEvolucionAnualPorts(
            conteo_gateway=get_conteo_tecnico_gateway(),
            input_repo=SqlAlchemyBonoTecnicoInputRepository(session),
            tareas_varias_gateway=SqlAlchemyTareasVariasGateway(session),
        )
    )


def build_get_mi_resumen_bono(session: AsyncSession) -> GetMiResumenBono:
    return GetMiResumenBono(
        SqlAlchemyTecnicoIdentityGateway(session),
        build_get_puntajes_periodo(session),
        SqlAlchemyTareasVariasGateway(session),
    )


def build_get_vinculo_siges(session: AsyncSession) -> GetVinculoSiges:
    return GetVinculoSiges(SqlAlchemyTecnicoIdentityGateway(session))
