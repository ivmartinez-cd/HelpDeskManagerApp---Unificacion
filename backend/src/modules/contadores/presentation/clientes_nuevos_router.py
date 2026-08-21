"""Fichas de clientes nuevos (onboarding de contadores): reemplaza el Excel
de la TL alimentado por el mail "Nuevo Negocio" de Comercial. La ficha es
local; Siges solo anota en lectura (instalaciones reales, contrato, rubro) y
sugiere candidatos (primer contrato reciente sin ficha). Todo bajo
`contadores.manage`: es una herramienta de gestión del equipo, no una vista
por operador (misma decisión que coberturas/anexos, 2026-08-21)."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.features import require_feature
from src.modules.contadores.application.dtos.cliente_nuevo_dtos import ClienteNuevoRequest
from src.modules.contadores.application.use_cases.create_cliente_nuevo import (
    CreateClienteNuevoUseCase,
)
from src.modules.contadores.application.use_cases.list_clientes_nuevos import (
    DEFAULT_VENTANA_CANDIDATOS_DIAS,
    ListCandidatosClientesNuevosUseCase,
    ListClientesNuevosDependencies,
    ListClientesNuevosUseCase,
)
from src.modules.contadores.application.use_cases.update_cliente_nuevo import (
    DeleteClienteNuevoUseCase,
    UpdateClienteNuevoUseCase,
)
from src.modules.contadores.domain.well_known_features import CLIENTES_NUEVOS
from src.modules.contadores.infrastructure.repositories.sqlalchemy_cliente_nuevo_repository import (  # noqa: E501
    SqlAlchemyClienteNuevoRepository,
)
from src.modules.contadores.presentation.dependencies import (
    get_clientes_nuevos_gateway_or_none,
)
from src.modules.contadores.presentation.schemas.clientes_nuevos_schemas import (
    CandidatosClientesNuevosResponse,
    ClienteNuevoIn,
    ClienteNuevoOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores/clientes-nuevos", tags=["contadores-clientes-nuevos"])

# Función concedible por usuario (ADR-032): antes contadores.manage.
_require_manage = Depends(require_feature(CLIENTES_NUEVOS))
# Son decenas de fichas por año: el listado se pide entero y se filtra en la
# UI, cumpliendo igual el contrato de paginación.
_MAX_PAGE_SIZE = 500


def _deps(db: AsyncSession) -> ListClientesNuevosDependencies:
    return ListClientesNuevosDependencies(
        repo=SqlAlchemyClienteNuevoRepository(db), siges=get_clientes_nuevos_gateway_or_none()
    )


@router.get("", response_model=Page[ClienteNuevoOut])
async def list_clientes_nuevos(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=_MAX_PAGE_SIZE),
    refresh: bool = Query(default=False, description="Fuerza re-consultar Siges"),
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ClienteNuevoOut]:
    results = await ListClientesNuevosUseCase(_deps(db)).execute(force_refresh=refresh)
    return Page.of([ClienteNuevoOut.from_result(r) for r in results], page=page, size=size)


@router.get("/candidatos", response_model=CandidatosClientesNuevosResponse)
async def list_candidatos(
    dias: int = Query(default=DEFAULT_VENTANA_CANDIDATOS_DIAS, ge=7, le=730),
    refresh: bool = Query(default=False),
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> CandidatosClientesNuevosResponse:
    result = await ListCandidatosClientesNuevosUseCase(_deps(db)).execute(
        hoy=datetime.now(UTC).date(), dias=dias, force_refresh=refresh
    )
    return CandidatosClientesNuevosResponse.from_result(result)


@router.post("", response_model=ClienteNuevoOut, status_code=status.HTTP_201_CREATED)
async def create_cliente_nuevo(
    body: ClienteNuevoIn,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ClienteNuevoOut:
    use_case = CreateClienteNuevoUseCase(SqlAlchemyClienteNuevoRepository(db))
    result = await use_case.execute(_to_app_request(body), created_by_user_id=identity.user.id)
    return ClienteNuevoOut.from_result(result)


@router.put("/{ficha_id}", response_model=ClienteNuevoOut)
async def update_cliente_nuevo(
    ficha_id: uuid.UUID,
    body: ClienteNuevoIn,
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ClienteNuevoOut:
    use_case = UpdateClienteNuevoUseCase(SqlAlchemyClienteNuevoRepository(db))
    result = await use_case.execute(ficha_id, _to_app_request(body))
    return ClienteNuevoOut.from_result(result)


@router.delete("/{ficha_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente_nuevo(
    ficha_id: uuid.UUID,
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await DeleteClienteNuevoUseCase(SqlAlchemyClienteNuevoRepository(db)).execute(ficha_id)


def _to_app_request(body: ClienteNuevoIn) -> ClienteNuevoRequest:
    return ClienteNuevoRequest(
        cliente=body.cliente,
        siges_empresa_id=body.siges_empresa_id,
        contrato_nro=body.contrato_nro,
        fecha_firma=body.fecha_firma,
        vendedor=body.vendedor,
        operador_id=body.operador_id,
        implementacion_servicio=body.implementacion_servicio,
        fecha_estimada_implementacion=body.fecha_estimada_implementacion,
        fecha_estimada_primera_facturacion=body.fecha_estimada_primera_facturacion,
        dia_corte=body.dia_corte,
        equipos_previstos=body.equipos_previstos,
        estado=body.estado,
        stc_enviado_el=body.stc_enviado_el,
        notas=body.notas,
    )
