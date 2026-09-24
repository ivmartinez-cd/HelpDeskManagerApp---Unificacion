"""Implementación Postgres del puerto RemitosDespachoRepository (`insumos_despacho_remito`
e `insumos_despacho_incidente`)."""

from collections import defaultdict
from collections.abc import Sequence
from itertools import batched
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.despachados.despacho_siges import (
    DespachoSiges,
    IncidenteInsumo,
)
from src.modules.insumos.infrastructure.models.despacho_remito_model import (
    DespachoIncidenteModel,
    DespachoRemitoModel,
)
from src.modules.insumos.infrastructure.repositories._lotes_despachos import (
    FILAS_POR_LOTE,
)

# `guia` también: si en Siges corrigen una guía mal tipeada, el remito pasa a la nueva
# (el envío de la guía nueva ya existe porque el alta de envíos va antes).
_COLUMNAS_REMITO_ACTUALIZABLES = (
    "guia",
    "numero_remito",
    "fecha_remito",
    "bultos",
    "id_distribucion",
    "cliente",
    "sucursal_cliente",
    "entrega_a",
)


class SqlAlchemyRemitosDespachoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, despachos: Sequence[DespachoSiges]) -> None:
        if not despachos:
            return
        await self._upsert_remitos(_filas_remito(despachos))
        await self._upsert_incidentes(_filas_incidente(despachos))
        await self._session.flush()

    async def listar_por_guia(self, guia: str) -> list[DespachoSiges]:
        stmt = (
            select(DespachoRemitoModel)
            .where(DespachoRemitoModel.guia == guia)
            .order_by(DespachoRemitoModel.fecha_remito, DespachoRemitoModel.id_remito)
        )
        remitos = (await self._session.execute(stmt)).scalars().all()
        incidentes = await self._incidentes_de([r.id_remito for r in remitos])
        return [_despacho(r, incidentes.get(r.id_remito, ())) for r in remitos]

    async def _upsert_remitos(self, filas: list[dict[str, Any]]) -> None:
        for lote in batched(filas, FILAS_POR_LOTE):
            stmt = pg_insert(DespachoRemitoModel).values(list(lote))
            await self._session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[DespachoRemitoModel.id_remito],
                    set_={c: stmt.excluded[c] for c in _COLUMNAS_REMITO_ACTUALIZABLES},
                )
            )

    async def _upsert_incidentes(self, filas: list[dict[str, Any]]) -> None:
        for lote in batched(filas, FILAS_POR_LOTE):
            stmt = pg_insert(DespachoIncidenteModel).values(list(lote))
            await self._session.execute(
                stmt.on_conflict_do_update(
                    index_elements=[
                        DespachoIncidenteModel.id_remito,
                        DespachoIncidenteModel.numero,
                    ],
                    set_={"numero_cliente": stmt.excluded.numero_cliente},
                )
            )

    async def _incidentes_de(self, ids_remito: list[int]) -> dict[int, tuple[IncidenteInsumo, ...]]:
        if not ids_remito:
            return {}
        stmt = (
            select(DespachoIncidenteModel)
            .where(DespachoIncidenteModel.id_remito.in_(ids_remito))
            .order_by(DespachoIncidenteModel.numero)
        )
        por_remito: defaultdict[int, list[IncidenteInsumo]] = defaultdict(list)
        for fila in (await self._session.execute(stmt)).scalars():
            por_remito[fila.id_remito].append(IncidenteInsumo(fila.numero, fila.numero_cliente))
        return {id_remito: tuple(lista) for id_remito, lista in por_remito.items()}


def _filas_remito(despachos: Sequence[DespachoSiges]) -> list[dict[str, Any]]:
    """Una fila por `id_remito` (si vino repetido gana el último): un mismo INSERT ... ON
    CONFLICT DO UPDATE no puede tocar dos veces la misma fila."""
    unicos = {d.id_remito: d for d in despachos}
    return [
        {"id_remito": d.id_remito, "guia": d.guia}
        | {c: getattr(d, c) for c in _COLUMNAS_REMITO_ACTUALIZABLES}
        for d in unicos.values()
    ]


def _filas_incidente(despachos: Sequence[DespachoSiges]) -> list[dict[str, Any]]:
    unicos = {(d.id_remito, i.numero): i for d in despachos for i in d.incidentes}
    return [
        {"id_remito": id_remito, "numero": numero, "numero_cliente": i.numero_cliente}
        for (id_remito, numero), i in unicos.items()
    ]


def _despacho(
    remito: DespachoRemitoModel, incidentes: tuple[IncidenteInsumo, ...]
) -> DespachoSiges:
    return DespachoSiges(
        id_remito=remito.id_remito,
        numero_remito=remito.numero_remito,
        guia=remito.guia,
        id_distribucion=remito.id_distribucion,
        fecha_remito=remito.fecha_remito,
        bultos=remito.bultos,
        cliente=remito.cliente,
        sucursal_cliente=remito.sucursal_cliente,
        entrega_a=remito.entrega_a,
        incidentes=incidentes,
    )
