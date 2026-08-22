"""SqlAlchemyMatchingDescarteRepository contra Postgres real: el descarte es
idempotente por (tabla_km_id, siges_sucursal_id) y se agrupa por fila."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_matching_descarte_repository import (  # noqa: E501
    SqlAlchemyMatchingDescarteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)


async def _tabla_km_id(db_session: AsyncSession, prestador_id: uuid.UUID) -> uuid.UUID:
    entrada = await SqlAlchemyTablaKmRepository(db_session).create(
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre="Empresa A",
        sucursal_nombre=f"Sucursal {uuid.uuid4().hex[:6]}",
        observaciones=None,
        domicilio_cliente=None,
        localidad_cliente=None,
        provincia_cliente=None,
        kms_recorrido=20.0,
        umbral_viatico=10.0,
        aplica_viatico=True,
        kms_a_facturar=20.0,
        url_maps=None,
    )
    return entrada.id


async def test_create_es_idempotente_y_list_agrupa_por_fila(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyMatchingDescarteRepository(db_session)
    fila_a = await _tabla_km_id(db_session, prestador_id)
    fila_b = await _tabla_km_id(db_session, prestador_id)
    sin_descartes = await _tabla_km_id(db_session, prestador_id)

    await repo.create(fila_a, 101, "op@canal.com")
    await repo.create(fila_a, 101, "otro@canal.com")  # mismo par: no duplica ni falla
    await repo.create(fila_a, 102, "op@canal.com")
    await repo.create(fila_b, 101, "op@canal.com")

    resultado = await repo.list_descartados_por_fila([fila_a, fila_b, sin_descartes])

    assert resultado == {fila_a: {101, 102}, fila_b: {101}}


async def test_list_descartados_con_lista_vacia_no_consulta(
    db_session: AsyncSession,
) -> None:
    assert await SqlAlchemyMatchingDescarteRepository(db_session).list_descartados_por_fila(
        []
    ) == {}
