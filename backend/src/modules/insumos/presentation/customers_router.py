"""Endpoints del módulo Clientes: lista, toggle, contactos por zona, importación."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneOverwriteRequest
from src.modules.insumos.domain.well_known_permissions import UPDATE, VIEW
from src.modules.insumos.presentation.dependencies.customers import (
    build_apply_zone_contacts_import,
    build_bulk_seed_contacts,
    build_bulk_toggle_customers,
    build_delete_zone_contact,
    build_get_customer_zones,
    build_get_sds_contacts,
    build_get_zone_contacts,
    build_import_contacts_from_supply,
    build_list_customers,
    build_preview_zone_contacts_import,
    build_set_zone_contact,
    build_sync_customers,
    build_toggle_customer,
)
from src.modules.insumos.presentation.schemas.customer_schemas import (
    BulkToggleBody,
    CustomerOut,
    CustomerPatchBody,
    ImportContactsResponse,
    ImportFromSupplyBody,
    OkResponse,
    SdsContactOut,
    SeedDefaultContactsBody,
    SeedResponse,
    SyncCustomersResponse,
    ZoneContactApplyBody,
    ZoneContactApplyResponse,
    ZoneContactBody,
    ZoneContactOut,
    ZoneContactPreviewResponse,
    ZoneContactPreviewRowOut,
)
from src.modules.insumos.presentation.wiring import get_insight_gateway
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> list[CustomerOut]:
    customers = await build_list_customers(db).execute()
    return [CustomerOut.from_domain(c) for c in customers]


@router.patch("/customers/{customer_id}", response_model=OkResponse)
async def patch_customer(
    customer_id: int,
    body: CustomerPatchBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    await build_toggle_customer(db).execute(customer_id, body.enabled)
    return OkResponse()


@router.post("/customers/bulk-toggle", response_model=OkResponse)
async def bulk_toggle_customers(
    body: BulkToggleBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    await build_bulk_toggle_customers(db).execute(body.enabled)
    return OkResponse()


@router.post("/sync-customers", response_model=SyncCustomersResponse)
async def sync_customers(
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SyncCustomersResponse:
    try:
        customers = await get_insight_gateway().get_customers()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="No se pudo sincronizar clientes desde Insight (verificar credenciales)",
        ) from exc
    count = await build_sync_customers(db).execute(customers)
    return SyncCustomersResponse(ok=True, count=count)


@router.get("/customers/{customer_id}/contacts", response_model=list[ZoneContactOut])
async def get_customer_contacts(
    customer_id: int,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> list[ZoneContactOut]:
    rows = await build_get_zone_contacts(db).execute(customer_id)
    return [ZoneContactOut.from_domain(r) for r in rows]


@router.put("/customers/{customer_id}/contacts", response_model=OkResponse)
async def put_customer_contacts(
    customer_id: int,
    body: ZoneContactBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    await build_set_zone_contact(db).execute(customer_id, body.to_domain_row())
    return OkResponse()


@router.delete("/customers/{customer_id}/contacts", response_model=OkResponse)
async def delete_customer_contacts(
    customer_id: int,
    zone: str = Query(default=""),
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    await build_delete_zone_contact(db).execute(customer_id, zone)
    return OkResponse()


@router.post("/customers/contacts/seed-default", response_model=SeedResponse)
async def seed_default_contacts(
    body: SeedDefaultContactsBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SeedResponse:
    updated = await build_bulk_seed_contacts(db).execute(
        body.customer_ids, body.to_domain_row()
    )
    return SeedResponse(ok=True, updated=updated)


@router.post(
    "/customers/{customer_id}/contacts/import-from-supply",
    response_model=ImportContactsResponse,
)
async def import_contacts_from_supply(
    customer_id: int,
    body: ImportFromSupplyBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> ImportContactsResponse:
    supply_id = body.parsed_supply_id()
    if supply_id is None:
        return ImportContactsResponse(ok=False, error=f"ID de supply inválido: {body.supply_id!r}")
    row = await build_import_contacts_from_supply(db).execute(customer_id, supply_id)
    if row is None:
        return ImportContactsResponse(
            ok=False, error=f"El SOAP no devolvió datos para el supply {supply_id}"
        )
    return ImportContactsResponse(ok=True, zone=row.zone, row=ZoneContactOut.from_domain(row))


@router.get("/customers/{customer_id}/sds-contacts", response_model=list[SdsContactOut])
async def get_customer_sds_contacts(
    customer_id: int,
    _: Identity = _require_view,
) -> list[SdsContactOut]:
    try:
        rows = await build_get_sds_contacts().execute(customer_id)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [SdsContactOut.from_domain(r) for r in rows]


@router.get("/customers/{customer_id}/zones", response_model=list[str])
async def get_customer_zones(
    customer_id: int,
    _: Identity = _require_view,
) -> list[str]:
    try:
        return await build_get_customer_zones().execute(customer_id)
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get(
    "/customers/{customer_id}/zone-contacts-import/preview",
    response_model=ZoneContactPreviewResponse,
)
async def preview_zone_contacts_import(
    customer_id: int,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> ZoneContactPreviewResponse:
    try:
        rows = await build_preview_zone_contacts_import(db).execute(customer_id)
    except Exception:
        return ZoneContactPreviewResponse(
            ok=False,
            error=(
                "No se pudo consultar Insight o el PortalWeb de SDS"
                " — verificar credenciales y conexión"
            ),
        )
    return ZoneContactPreviewResponse(
        ok=True, rows=[ZoneContactPreviewRowOut.from_domain(r) for r in rows]
    )


@router.post(
    "/customers/{customer_id}/zone-contacts-import/apply",
    response_model=ZoneContactApplyResponse,
)
async def apply_zone_contacts_import(
    customer_id: int,
    body: ZoneContactApplyBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> ZoneContactApplyResponse:
    requested = [ZoneOverwriteRequest(zone=r.zone, overwrite=r.overwrite) for r in body.rows]
    try:
        applied = await build_apply_zone_contacts_import(db).execute(customer_id, requested)
    except Exception:
        return ZoneContactApplyResponse(
            ok=False,
            error=(
                "No se pudo consultar Insight o el PortalWeb de SDS"
                " — verificar credenciales y conexión"
            ),
        )
    return ZoneContactApplyResponse(ok=True, applied=applied)
