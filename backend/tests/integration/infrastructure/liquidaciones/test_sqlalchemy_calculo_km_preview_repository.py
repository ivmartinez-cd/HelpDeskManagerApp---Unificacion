"""SqlAlchemyCalculoKmPreviewRepository contra Postgres real: solo sobrevive
la última propuesta por prestador, y el payload de filas hace round trip."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.calculo_km_preview import PreviewFila
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_calculo_km_preview_repository import (  # noqa: E501
    SqlAlchemyCalculoKmPreviewRepository,
)


def _fila(accion: str, tabla_km_id: uuid.UUID | None) -> PreviewFila:
    return PreviewFila(
        accion=accion,
        tabla_km_id=tabla_km_id,
        siges_sucursal_id=123,
        empresa_nombre="Cencosud",
        sucursal_nombre="Jumbo",
        domicilio="Av. Santa Fe 4000",
        localidad="CABA",
        provincia="Buenos Aires",
        coords_origen="siges",
        latitud_destino=-34.58,
        longitud_destino=-58.42,
        latitud_base=-34.60,
        longitud_base=-58.38,
        kms_ida=5.5,
        kms_vuelta=6.0,
        kms_total=11.5,
        umbral_viatico=10.0,
        aplica_viatico=True,
        kms_a_facturar=11.5,
        kms_recorrido_actual=10.0 if accion == "actualizar" else None,
        kms_a_facturar_actual=10.0 if accion == "actualizar" else None,
    )


async def test_create_reemplaza_el_preview_anterior_del_prestador(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyCalculoKmPreviewRepository(db_session)
    primero = await repo.create(
        prestador_id=prestador_id,
        filas=(_fila("crear", None),),
        sin_ubicar=1,
        sin_ruta=0,
        elementos_google=1,
        sin_actividad=0,
    )
    segundo = await repo.create(
        prestador_id=prestador_id,
        filas=(_fila("actualizar", uuid.uuid4()), _fila("crear", None)),
        sin_ubicar=0,
        sin_ruta=2,
        elementos_google=4,
        sin_actividad=3,
    )

    assert await repo.get_by_id(primero.id) is None
    leido = await repo.get_by_id(segundo.id)
    assert leido is not None
    assert leido.prestador_id == prestador_id
    assert (leido.sin_ubicar, leido.sin_ruta, leido.elementos_google, leido.sin_actividad) == (
        0, 2, 4, 3,
    )
    assert leido.filas == segundo.filas
    assert leido.filas[0].accion == "actualizar"
    assert leido.filas[0].tabla_km_id is not None
    assert leido.filas[1].tabla_km_id is None
    assert leido.filas[1].kms_recorrido_actual is None


async def test_delete_devuelve_si_existia(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyCalculoKmPreviewRepository(db_session)
    preview = await repo.create(
        prestador_id=prestador_id,
        filas=(),
        sin_ubicar=0,
        sin_ruta=0,
        elementos_google=0,
        sin_actividad=0,
    )

    assert await repo.delete(preview.id) is True
    assert await repo.get_by_id(preview.id) is None
    assert await repo.delete(preview.id) is False
