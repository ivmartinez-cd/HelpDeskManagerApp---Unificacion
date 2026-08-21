import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.dtos.ausencia_dtos import ListarAusenciasQuery
from src.modules.vacaciones.application.use_cases.decidir_ausencia import (
    DecidirAusencia,
    DecidirAusenciaDependencies,
)
from src.modules.vacaciones.application.use_cases.gestionar_ausencias import (
    AusenciasDependencies,
    CrearAusencias,
    EditarAusencia,
    EliminarAusencia,
)
from src.modules.vacaciones.application.use_cases.leer_ausencias import (
    LeerAusenciasDependencies,
    ListarAusencias,
)
from src.modules.vacaciones.application.use_cases.reporte_descuentos import (
    ReporteDescuentos,
    ReporteDescuentosDependencies,
)
from src.modules.vacaciones.domain.entities.ausencia import TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.well_known_permissions import APPROVE, CREATE, VIEW
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyRegistradorAuditoria,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ausencia_repository import (  # noqa: E501
    SqlAlchemyAusenciaRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_cargo_repository import (
    SqlAlchemyCargoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_feriado_repository import (
    SqlAlchemyFeriadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_impacto_turnos_lookup import (  # noqa: E501
    SqlAlchemyImpactoTurnosLookup,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_repository import (
    SqlAlchemySectorRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (  # noqa: E501
    SqlAlchemySolicitudRepository,
)
from src.modules.vacaciones.presentation.dependencies.actor import get_actor_vacaciones
from src.modules.vacaciones.presentation.schemas.ausencia_schemas import (
    AusenciaResponse,
    CrearAusenciaRequest,
    DecidirAusenciaRequest,
    DecisionAusenciaResponse,
    DescuentoRowResponse,
    EditarAusenciaRequest,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones/ausencias", tags=["vacaciones"])

_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_create = Depends(require_permission(CREATE))
_require_approve = Depends(require_permission(APPROVE))


def _write_deps(db: AsyncSession, actor: ActorVacaciones) -> AusenciasDependencies:
    return AusenciasDependencies(
        ausencias=SqlAlchemyAusenciaRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        solicitudes=SqlAlchemySolicitudRepository(db),
        auditoria=SqlAlchemyRegistradorAuditoria(db, actor.user_id),
    )


def _read_deps(db: AsyncSession) -> LeerAusenciasDependencies:
    return LeerAusenciasDependencies(
        ausencias=SqlAlchemyAusenciaRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
    )


@router.get("")
async def list_ausencias(
    status_filter: EstadoSolicitud | None = Query(default=None, alias="status"),
    tipo: TipoAusencia | None = Query(default=None),
    empleado_id: uuid.UUID | None = Query(default=None, alias="empleadoId"),
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[AusenciaResponse]:
    query = ListarAusenciasQuery(
        status=status_filter, tipo=tipo, empleado_id=empleado_id, desde=desde, hasta=hasta
    )
    dtos = await ListarAusencias(_read_deps(db)).execute(query, actor)
    return Page.of([AusenciaResponse.from_dto(d) for d in dtos], page=page, size=size)


@router.get("/reportes/descuentos")
async def reporte_descuentos(
    year: int = Query(),
    month: int = Query(ge=1, le=12),
    department_id: uuid.UUID | None = Query(default=None, alias="departmentId"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_approve,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[DescuentoRowResponse]:
    deps = ReporteDescuentosDependencies(
        ausencias=SqlAlchemyAusenciaRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        cargos=SqlAlchemyCargoRepository(db),
        feriados=SqlAlchemyFeriadoRepository(db),
    )
    rows = await ReporteDescuentos(deps).execute(year, month, department_id, actor)
    return Page.of([DescuentoRowResponse.from_dto(r) for r in rows], page=page, size=size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_ausencias(
    body: CrearAusenciaRequest,
    _identity: Identity = _require_create,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, list[uuid.UUID]]:
    creadas = await CrearAusencias(_write_deps(db, actor)).execute(body.to_command(), actor)
    return {"ids": [a.id for a in creadas]}


@router.put("/{ausencia_id}")
async def editar_ausencia(
    ausencia_id: uuid.UUID,
    body: EditarAusenciaRequest,
    _identity: Identity = _require_create,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, uuid.UUID]:
    ausencia = await EditarAusencia(_write_deps(db, actor)).execute(
        ausencia_id, body.to_command(), actor
    )
    return {"id": ausencia.id}


@router.delete("/{ausencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_ausencia(
    ausencia_id: uuid.UUID,
    _identity: Identity = _require_create,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await EliminarAusencia(_write_deps(db, actor)).execute(ausencia_id, actor)


@router.post("/{ausencia_id}/decision")
async def decidir_ausencia(
    ausencia_id: uuid.UUID,
    body: DecidirAusenciaRequest,
    _identity: Identity = _require_approve,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DecisionAusenciaResponse:
    """Aprobar/rechazar una baja pedida por un empleado (home office, cambio de
    horario…): mismo circuito que las solicitudes de vacaciones."""
    deps = DecidirAusenciaDependencies(
        ausencias=SqlAlchemyAusenciaRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        auditoria=SqlAlchemyRegistradorAuditoria(db, actor.user_id),
        impacto_turnos=SqlAlchemyImpactoTurnosLookup(db),
    )
    resultado = await DecidirAusencia(deps).execute(ausencia_id, body.to_command(), actor)
    return DecisionAusenciaResponse.build(
        resultado.ausencia.id, resultado.ausencia.status.value, resultado.afecta_turnos
    )
