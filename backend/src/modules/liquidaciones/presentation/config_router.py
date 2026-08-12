"""Endpoints de configuración de liquidaciones — prestadores, SPSTs, tarifarios y tabla KM.

Todos comparten el prefijo /api/liquidaciones. Las rutas con segmento literal
(prestadores/export, spsts/export, etc.) van antes de las que usan {id} para
evitar que FastAPI intente parsear "export" como UUID.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import CREATE, UPDATE, VIEW
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (
    SqlAlchemyTarifarioRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv as csv_helpers
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    PrestadorIn,
    PrestadorOut,
    SpstIn,
    SpstOut,
    TablaKmIn,
    TablaKmOut,
    TarifarioIn,
    TarifarioOut,
    ToggleActivoIn,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones-config"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_create = Depends(require_permission(CREATE))


# ══════════════════════════════════════════════════════════════════════════════
# Prestadores
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/prestadores", response_model=PrestadorOut, status_code=201)
async def create_prestador(
    body: PrestadorIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    prestador = await SqlAlchemyPrestadorRepository(db).create(
        nombre=body.nombre,
        nombre_corto=body.nombre_corto.strip().upper(),
        cuit=body.cuit or None,
        region=body.region or None,
    )
    return PrestadorOut.from_entity(prestador)


@router.patch("/prestadores/{prestador_id}", response_model=PrestadorOut)
async def update_prestador(
    prestador_id: UUID,
    body: PrestadorIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    updated = await SqlAlchemyPrestadorRepository(db).update(
        prestador_id,
        nombre=body.nombre,
        nombre_corto=body.nombre_corto.strip().upper(),
        cuit=body.cuit or None,
        region=body.region or None,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")
    return PrestadorOut.from_entity(updated)


@router.patch("/prestadores/{prestador_id}/activo", response_model=PrestadorOut)
async def toggle_prestador_activo(
    prestador_id: UUID,
    body: ToggleActivoIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    updated = await SqlAlchemyPrestadorRepository(db).toggle_activo(
        prestador_id, activo=body.activo
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")
    return PrestadorOut.from_entity(updated)


@router.get("/prestadores/export")
async def export_prestadores_csv(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    rows = await SqlAlchemyPrestadorRepository(db).list_all()
    return csv_helpers.export_prestadores(rows)


@router.post("/prestadores/import")
async def import_prestadores_csv(
    file: UploadFile = File(...),
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_prestadores(file, SqlAlchemyPrestadorRepository(db))


# ══════════════════════════════════════════════════════════════════════════════
# SPSTs
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/spsts", response_model=list[SpstOut])
async def list_spsts(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    solo_activos: bool = Query(default=False, alias="soloActivos"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> list[SpstOut]:
    rows = await SqlAlchemySpstRepository(db).list_all(
        prestador_id=prestador_id, solo_activos=solo_activos
    )
    return [SpstOut.from_entity(s) for s in rows]


@router.post("/spsts", response_model=SpstOut, status_code=201)
async def create_spst(
    body: SpstIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    spst = await SqlAlchemySpstRepository(db).create(
        prestador_id=body.prestador_id,
        nombre=body.nombre,
        domicilio=body.domicilio or None,
        localidad=body.localidad or None,
        provincia=body.provincia or None,
        zona=body.zona or None,
    )
    return SpstOut.from_entity(spst)


@router.patch("/spsts/{spst_id}", response_model=SpstOut)
async def update_spst(
    spst_id: UUID,
    body: SpstIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    updated = await SqlAlchemySpstRepository(db).update(
        spst_id,
        nombre=body.nombre,
        domicilio=body.domicilio or None,
        localidad=body.localidad or None,
        provincia=body.provincia or None,
        zona=body.zona or None,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="SPST no encontrado")
    return SpstOut.from_entity(updated)


@router.patch("/spsts/{spst_id}/activo", response_model=SpstOut)
async def toggle_spst_activo(
    spst_id: UUID,
    body: ToggleActivoIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    updated = await SqlAlchemySpstRepository(db).toggle_activo(spst_id, activo=body.activo)
    if not updated:
        raise HTTPException(status_code=404, detail="SPST no encontrado")
    return SpstOut.from_entity(updated)


@router.get("/spsts/export")
async def export_spsts_csv(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    prest_repo = SqlAlchemyPrestadorRepository(db)
    spst_repo = SqlAlchemySpstRepository(db)
    prestadores = await prest_repo.list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    return csv_helpers.export_spsts(await spst_repo.list_all(), pmap)


@router.post("/spsts/import")
async def import_spsts_csv(
    file: UploadFile = File(...),
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_spsts(
        file, SqlAlchemySpstRepository(db), SqlAlchemyPrestadorRepository(db)
    )


# ══════════════════════════════════════════════════════════════════════════════
# Tarifarios
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/tarifarios", response_model=list[TarifarioOut])
async def list_tarifarios(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> list[TarifarioOut]:
    repo = SqlAlchemyTarifarioRepository(db)
    rows = await (repo.list_by_prestador(prestador_id) if prestador_id else repo.list_all())
    return [TarifarioOut.from_entity(t) for t in rows]


@router.post("/tarifarios", response_model=TarifarioOut, status_code=201)
async def create_tarifario(
    body: TarifarioIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> TarifarioOut:
    tarifario = await SqlAlchemyTarifarioRepository(db).create(
        prestador_id=body.prestador_id,
        tipo_servicio=body.tipo_servicio,
        zona=body.zona or None,
        costo_servicio=body.costo_servicio,
        costo_km=body.costo_km,
        vigencia_desde=body.vigencia_desde,
        vigencia_hasta=body.vigencia_hasta,
    )
    return TarifarioOut.from_entity(tarifario)


@router.delete("/tarifarios/{tarifario_id}", status_code=204)
async def delete_tarifario(
    tarifario_id: UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await SqlAlchemyTarifarioRepository(db).delete(tarifario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tarifario no encontrado")


@router.get("/tarifarios/export")
async def export_tarifarios_csv(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    prestadores = await SqlAlchemyPrestadorRepository(db).list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    rows = await SqlAlchemyTarifarioRepository(db).list_all()
    return csv_helpers.export_tarifarios(rows, pmap)


@router.post("/tarifarios/import")
async def import_tarifarios_csv(
    file: UploadFile = File(...),
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_tarifarios(
        file, SqlAlchemyTarifarioRepository(db), SqlAlchemyPrestadorRepository(db)
    )


# ══════════════════════════════════════════════════════════════════════════════
# Tabla KM
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/tabla-km", response_model=list[TablaKmOut])
async def list_tabla_km(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    q: str | None = Query(default=None),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> list[TablaKmOut]:
    rows = await SqlAlchemyTablaKmRepository(db).list_all(prestador_id=prestador_id, q=q)
    return [TablaKmOut.from_entity(t) for t in rows]


@router.post("/tabla-km", response_model=TablaKmOut, status_code=201)
async def create_tabla_km(
    body: TablaKmIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> TablaKmOut:
    row = await SqlAlchemyTablaKmRepository(db).create(
        prestador_id=body.prestador_id,
        spst_id=body.spst_id,
        empresa_nombre=body.empresa_nombre,
        sucursal_nombre=body.sucursal_nombre,
        observaciones=body.observaciones,
        domicilio_cliente=body.domicilio_cliente,
        localidad_cliente=body.localidad_cliente,
        provincia_cliente=body.provincia_cliente,
        kms_recorrido=body.kms_recorrido,
        umbral_viatico=body.umbral_viatico,
        aplica_viatico=body.aplica_viatico,
        kms_a_facturar=body.kms_a_facturar,
        url_maps=body.url_maps,
    )
    return TablaKmOut.from_entity(row)


@router.delete("/tabla-km/{tabla_km_id}", status_code=204)
async def delete_tabla_km(
    tabla_km_id: UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await SqlAlchemyTablaKmRepository(db).delete(tabla_km_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrada de Tabla KM no encontrada")


@router.get("/tabla-km/export")
async def export_tabla_km_csv(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    prestadores = await SqlAlchemyPrestadorRepository(db).list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    rows = await SqlAlchemyTablaKmRepository(db).list_all()
    return csv_helpers.export_tabla_km(rows, pmap)


@router.post("/tabla-km/import")
async def import_tabla_km_csv(
    file: UploadFile = File(...),
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_tabla_km(
        file, SqlAlchemyTablaKmRepository(db), SqlAlchemyPrestadorRepository(db)
    )
