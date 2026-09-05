"""Endpoints de configuración de tabla KM (/api/liquidaciones/tabla-km)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.application.use_cases.config_tabla_km import TablaKmDatos
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv_export as csv_export
from src.modules.liquidaciones.presentation import (
    _liq_csv_upsert_tabla_km as csv_helpers,
)
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_export,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.config_routers._reanalisis import (
    reanalizar_abiertas,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_asignar_zona_sucursal,
    build_create_tabla_km,
    build_delete_tabla_km,
    build_fijar_km_referencia,
    build_set_archivada_tabla_km,
    build_update_tabla_km,
    build_vincular_tabla_km_spst,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    ResultadoVinculoTablaKmSpstOut,
    TablaKmIn,
    TablaKmOut,
)
from src.modules.liquidaciones.presentation.schemas.tabla_km_schemas import (
    ArchivadaIn,
    AsignarZonaSucursalIn,
    KmReferenciaIn,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


def _datos(body: TablaKmIn) -> TablaKmDatos:
    return TablaKmDatos(
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


@router.get("/tabla-km", response_model=Page[TablaKmOut])
async def list_tabla_km(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[TablaKmOut]:
    rows = await SqlAlchemyTablaKmRepository(db).list_all(prestador_id=prestador_id, q=q)
    return Page.of([TablaKmOut.from_entity(t) for t in rows], page=page, size=size)


@router.post("/tabla-km", response_model=TablaKmOut, status_code=201)
async def create_tabla_km(
    body: TablaKmIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    row = await build_create_tabla_km(db).execute(_datos(body))
    await reanalizar_abiertas(db, row.prestador_id)
    return TablaKmOut.from_entity(row)


@router.patch("/tabla-km/{tabla_km_id}", response_model=TablaKmOut)
async def update_tabla_km(
    tabla_km_id: UUID,
    body: TablaKmIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    updated = await build_update_tabla_km(db).execute(tabla_km_id, _datos(body))
    await reanalizar_abiertas(db, updated.prestador_id)
    return TablaKmOut.from_entity(updated)


@router.delete("/tabla-km/{tabla_km_id}", status_code=204)
async def delete_tabla_km(
    tabla_km_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    borrada = await build_delete_tabla_km(db).execute(tabla_km_id)
    await reanalizar_abiertas(db, borrada.prestador_id)


@router.post("/tabla-km/vincular-spst", response_model=ResultadoVinculoTablaKmSpstOut)
async def vincular_spst(
    prestador_id: UUID = Query(alias="prestadorId"),
    dry_run: bool = Query(default=True, alias="dryRun"),
    incluir_provincia: bool = Query(default=False, alias="incluirProvincia"),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ResultadoVinculoTablaKmSpstOut:
    """Vincula filas de Tabla KM sin `spst_id` al SPST del mismo prestador cuya
    zona/localidad matchea la localidad del cliente (y, con `incluirProvincia`,
    también por provincia única) — ver `domain/services/vincular_tabla_km_spst.py`.
    Dry-run por default."""
    resultado = await build_vincular_tabla_km_spst(db).execute(
        prestador_id, dry_run=dry_run, incluir_provincia=incluir_provincia
    )
    if resultado.vinculadas:
        await reanalizar_abiertas(db, prestador_id)
    return ResultadoVinculoTablaKmSpstOut.from_dto(resultado)


@router.put("/tabla-km/zona-sucursal", response_model=TablaKmOut)
async def asignar_zona_sucursal(
    body: AsignarZonaSucursalIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    """Fija la zona (SPST o Genérica) de la fila de Tabla KM de un par
    empresa+sucursal, desde la alerta ALT008 del detalle — todos los incidentes
    de esa sucursal comparten la fila. Reanaliza las liquidaciones abiertas."""
    fila = await build_asignar_zona_sucursal(db).execute(
        body.prestador_id,
        empresa_nombre=body.empresa_nombre,
        sucursal_nombre=body.sucursal_nombre,
        spst_id=body.spst_id,
    )
    await reanalizar_abiertas(db, body.prestador_id)
    return TablaKmOut.from_entity(fila)


@router.put("/tabla-km/km-referencia", response_model=TablaKmOut)
async def fijar_km_referencia(
    body: KmReferenciaIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    """Toma los km cobrados por el prestador como referencia de la sucursal
    (desde la alerta ALT002 "sin km de referencia"). Reanaliza las abiertas."""
    fila = await build_fijar_km_referencia(db).execute(
        body.prestador_id,
        empresa_nombre=body.empresa_nombre,
        sucursal_nombre=body.sucursal_nombre,
        kms=body.kms,
    )
    await reanalizar_abiertas(db, body.prestador_id)
    return TablaKmOut.from_entity(fila)


@router.patch("/tabla-km/{tabla_km_id}/archivada", response_model=TablaKmOut)
async def set_archivada_tabla_km(
    tabla_km_id: UUID,
    body: ArchivadaIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    fila = await build_set_archivada_tabla_km(db).execute(tabla_km_id, archivada=body.archivada)
    return TablaKmOut.from_entity(fila)


@router.get("/tabla-km/export")
async def export_tabla_km_csv(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = require_export,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> StreamingResponse:
    """Sin `prestadorId` exporta el catálogo completo. Con él (el caso normal desde
    la pantalla, que siempre tiene un prestador filtrado), exporta solo el suyo —
    antes ignoraba el filtro y siempre traía todo, rompiendo el ciclo "exporto lo
    que veo, corrijo, reimporto"."""
    repo = SqlAlchemyTablaKmRepository(db)
    rows = await (repo.list_by_prestador(prestador_id) if prestador_id else repo.list_all())
    prestadores = await SqlAlchemyPrestadorRepository(db).list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    return csv_export.export_tabla_km(rows, pmap)


@router.post("/tabla-km/import")
async def import_tabla_km_csv(
    file: UploadFile = File(...),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, int]:
    """El CSV no trae columna de SPST — sin esto, cada fila importada quedaría
    sin zona/tarifa hasta que alguien corriera "Vincular SPST" a mano. Se corre
    acá mismo, por cada prestador que recibió filas nuevas, mismo criterio
    "solo cuando hay un único candidato" que el botón manual."""
    resultado, prestadores_tocados = await csv_helpers.import_tabla_km(
        file,
        build_create_tabla_km(db),
        build_update_tabla_km(db),
        SqlAlchemyPrestadorRepository(db),
        SqlAlchemyTablaKmRepository(db),
    )
    for prestador_id in prestadores_tocados:
        await build_vincular_tabla_km_spst(db).execute(prestador_id, dry_run=False)
        await reanalizar_abiertas(db, prestador_id)
    return resultado
