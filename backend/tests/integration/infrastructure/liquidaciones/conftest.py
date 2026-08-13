"""Fixtures compartidas: cadena prestador -> liquidacion -> incidente, la más usada
por los tests de repos transaccionales de este módulo."""

import uuid
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)


def incidente_importado(**overrides: Any) -> IncidenteImportado:
    base: dict[str, Any] = dict(
        numero_incidente="INC-1",
        rubro="Rubro",
        tipo="correctivo",
        empresa_nombre="Empresa",
        sucursal_nombre="Sucursal",
        nro_serie="SN-1",
        fecha_cierre=None,
        costo_servicio_cobrado=100.0,
        cant_km_cobrado=10.0,
        costo_km_cobrado=5.0,
        total_viaje_cobrado=50.0,
        costo_total_cobrado=150.0,
        pasa_it=True,
    )
    base.update(overrides)
    return IncidenteImportado(**base)


@pytest_asyncio.fixture
async def prestador_id(db_session: AsyncSession) -> uuid.UUID:
    prestador = await SqlAlchemyPrestadorRepository(db_session).create(
        nombre="Prestador Test", nombre_corto="PTEST", cuit=None, region=None
    )
    return prestador.id


@pytest_asyncio.fixture
async def liquidacion_id(db_session: AsyncSession, prestador_id: uuid.UUID) -> uuid.UUID:
    liquidacion = await SqlAlchemyLiquidacionRepository(db_session).create(
        prestador_id=prestador_id,
        numero_liquidacion="1234-5",
        periodo="2026-01",
        tipo_liquidacion="regular",
        nombre_archivo=None,
        total_incidentes=0,
        total_importe=0.0,
    )
    return liquidacion.id


@pytest_asyncio.fixture
async def incidente_id(db_session: AsyncSession, liquidacion_id: uuid.UUID) -> uuid.UUID:
    incidentes = await SqlAlchemyIncidenteRepository(db_session).bulk_create(
        liquidacion_id, [incidente_importado()]
    )
    return incidentes[0].id
