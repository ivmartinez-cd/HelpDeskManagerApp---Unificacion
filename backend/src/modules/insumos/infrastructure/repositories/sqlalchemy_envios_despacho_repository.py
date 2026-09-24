"""Implementación Postgres del puerto EnviosDespachoRepository (`insumos_despacho_envio`)."""

from collections.abc import Collection, Sequence
from itertools import batched

from sqlalchemy import Select, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.despachados.envio_seguido import EnvioSeguido
from src.modules.insumos.infrastructure.models.despacho_envio_model import DespachoEnvioModel
from src.modules.insumos.infrastructure.repositories._lotes_despachos import (
    FILAS_POR_LOTE,
)
from src.modules.insumos.infrastructure.repositories.mapeo_envio_despacho import (
    columnas_alta,
    columnas_seguimiento,
    envio_desde_fila,
)


class SqlAlchemyEnviosDespachoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guias_seguidas(self, guias: Collection[str]) -> set[str]:
        if not guias:
            return set()
        stmt = select(DespachoEnvioModel.guia).where(DespachoEnvioModel.guia.in_(list(guias)))
        return set((await self._session.execute(stmt)).scalars().all())

    async def crear(self, envios: Sequence[EnvioSeguido]) -> None:
        if not envios:
            return
        for lote in batched(envios, FILAS_POR_LOTE):
            stmt = pg_insert(DespachoEnvioModel).values([columnas_alta(e) for e in lote])
            await self._session.execute(
                stmt.on_conflict_do_nothing(index_elements=[DespachoEnvioModel.guia])
            )
        await self._session.flush()

    async def listar_abiertos(self) -> list[EnvioSeguido]:
        stmt = (
            _leer_envios()
            .where(DespachoEnvioModel.abierto)
            .order_by(DespachoEnvioModel.fecha_remito, DespachoEnvioModel.guia)
        )
        filas = (await self._session.execute(stmt)).scalars().all()
        return [envio_desde_fila(fila) for fila in filas]

    async def obtener(self, guia: str) -> EnvioSeguido | None:
        stmt = _leer_envios().where(DespachoEnvioModel.guia == guia)
        fila = (await self._session.execute(stmt)).scalar_one_or_none()
        return None if fila is None else envio_desde_fila(fila)

    async def actualizar(self, envio: EnvioSeguido) -> None:
        """Escribe el seguimiento completo, cierre de alerta incluido: `envio` tiene que salir
        de un `obtener` reciente, no de una copia vieja (pisaría un cierre hecho entretanto)."""
        # clock_timestamp() y no now(): now() es la hora de inicio de la transacción.
        stmt = (
            update(DespachoEnvioModel)
            .where(DespachoEnvioModel.guia == envio.guia)
            .values(**columnas_seguimiento(envio), actualizado_en=func.clock_timestamp())
        )
        await self._session.execute(stmt)
        await self._session.flush()


def _leer_envios() -> Select[tuple[DespachoEnvioModel]]:
    """SELECT de envíos que siempre devuelve lo que hay en la base.

    Sin `populate_existing`, una fila que siga viva en el identity map de la sesión (algo
    retiene el modelo; con `expire_on_commit=False` nunca se vence) vuelve con los valores de
    cuando se cargó, aunque otro request o el ON DELETE SET NULL del usuario del cierre la
    hayan cambiado. Releer con `obtener` antes de `actualizar` depende de esto.
    """
    return select(DespachoEnvioModel).execution_options(populate_existing=True)
