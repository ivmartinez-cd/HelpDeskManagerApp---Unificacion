"""Armado de las dependencias de las acciones del operador sobre la Proyección
(ADR-044): los routers las piden acá y las pasan a application."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.dtos.decision_operador_dto import LecturaElegidaDto
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import (
    releer_lecturas_de_siges,
)
from src.modules.contadores.application.use_cases.proyeccion_operador.dependencias import (
    DependenciasProyeccion,
    OperadorProyeccion,
)
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    get_decisiones_operador_store,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_decisiones_operador_repository import (  # noqa: E501
    SqlAlchemyDecisionesOperadorRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_estim_log_repository import (
    SqlAlchemyEstimLogRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_recesos_repository import (
    SqlAlchemyRecesosRepository,
)
from src.modules.contadores.presentation.dependencies import (
    get_candidatos_equipo_gateway,
    get_grilla_estimacion_gateway,
)


def dependencias_proyeccion(db: AsyncSession) -> DependenciasProyeccion:
    """Lo que necesitan las acciones del operador sobre la Proyección (ADR-044)."""

    async def releer(id_maquina: int, clase: str) -> dict[int, LecturaElegidaDto]:
        return await releer_lecturas_de_siges(get_candidatos_equipo_gateway())(id_maquina, clase)

    return DependenciasProyeccion(
        decisiones_reales=SqlAlchemyDecisionesOperadorRepository(db),
        decisiones_ejemplo=get_decisiones_operador_store(),
        constructor_siges=lambda: ConstructorEntradaSiges(
            get_grilla_estimacion_gateway(), SqlAlchemyRecesosRepository(db)
        ),
        releer_siges=releer,
        estim_log=SqlAlchemyEstimLogRepository(db),
    )


def operador_de(identity: Identity) -> str:
    """Cada operador trabaja sobre SU última carga de la grilla (en v1.7, la
    lista en memoria de su circuito): es la clave con que el gateway la
    recuerda."""
    return str(identity.user.id)


def operador_proyeccion(identity: Identity) -> OperadorProyeccion:
    return OperadorProyeccion(user_id=identity.user.id, email=identity.user.email)
