"""Implementación Postgres del puerto PrestadorRepository (tabla prestadores)."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.errors import (
    CdVinculoDuplicadoError,
    PrestadorConLiquidacionesError,
    PrestadorDuplicadoError,
    SigesVinculoDuplicadoError,
)
from src.modules.liquidaciones.infrastructure.models.prestador_model import (
    LiquidacionPrestadorModel,
)


class SqlAlchemyPrestadorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prestador_id: UUID) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        return _to_entity(row) if row else None

    async def get_by_nombre_corto(self, nombre_corto: str) -> Prestador | None:
        stmt = select(LiquidacionPrestadorModel).where(
            LiquidacionPrestadorModel.nombre_corto == nombre_corto
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_all(self, *, solo_activos: bool = False) -> list[Prestador]:
        stmt = select(LiquidacionPrestadorModel).order_by(LiquidacionPrestadorModel.nombre)
        if solo_activos:
            stmt = stmt.where(LiquidacionPrestadorModel.activo.is_(True))
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def create(
        self, *, nombre: str, nombre_corto: str, cuit: str | None, region: str | None
    ) -> Prestador:
        model = LiquidacionPrestadorModel(
            id=uuid.uuid4(),
            nombre=nombre,
            nombre_corto=nombre_corto,
            cuit=cuit,
            region=region,
        )
        self._session.add(model)
        # El único UNIQUE que puede fallar en el alta es `nombre_corto` (los ids
        # de Siges/CD se cargan después, por `vincular_*`).
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise PrestadorDuplicadoError(nombre_corto) from exc
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(
        self,
        prestador_id: UUID,
        *,
        nombre: str,
        nombre_corto: str,
        cuit: str | None,
        region: str | None,
    ) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.nombre, row.nombre_corto, row.cuit, row.region = nombre, nombre_corto, cuit, region
        row.updated_at = datetime.now(UTC)
        await self._flush_o_duplicado(nombre_corto)
        await self._session.refresh(row)
        return _to_entity(row)

    async def _flush_o_duplicado(self, nombre_corto: str) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise PrestadorDuplicadoError(nombre_corto) from exc

    async def toggle_activo(self, prestador_id: UUID, *, activo: bool) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.activo = activo
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def list_con_cd_id(self) -> list[Prestador]:
        stmt = (
            select(LiquidacionPrestadorModel)
            .where(
                LiquidacionPrestadorModel.cd_prestador_id.is_not(None),
                LiquidacionPrestadorModel.activo.is_(True),
            )
            .order_by(LiquidacionPrestadorModel.nombre)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def get_by_cd_id(self, cd_id: int) -> Prestador | None:
        stmt = select(LiquidacionPrestadorModel).where(
            LiquidacionPrestadorModel.cd_prestador_id == cd_id
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def vincular_cd(
        self, prestador_id: UUID, *, cd_prestador_id: int | None
    ) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.cd_prestador_id = cd_prestador_id
        row.updated_at = datetime.now(UTC)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise CdVinculoDuplicadoError(cd_prestador_id) from exc
        await self._session.refresh(row)
        return _to_entity(row)

    async def vincular_base_sucursal(
        self, prestador_id: UUID, *, siges_base_sucursal_id: int | None
    ) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.siges_base_sucursal_id = siges_base_sucursal_id
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def vincular_siges(
        self, prestador_id: UUID, *, siges_empresa_id: int | None
    ) -> Prestador | None:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if not row:
            return None
        row.siges_empresa_id = siges_empresa_id
        row.updated_at = datetime.now(UTC)
        # flush() explícito para atrapar acá la violación del UNIQUE (mismo
        # criterio que delete()): un id de Siges solo puede vincular a un prestador.
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise SigesVinculoDuplicadoError(siges_empresa_id) from exc
        await self._session.refresh(row)
        return _to_entity(row)

    async def delete(self, prestador_id: UUID) -> bool:
        row = await self._session.get(LiquidacionPrestadorModel, prestador_id)
        if row is None:
            return False
        await self._session.delete(row)
        # `flush()` explícito (no basta con dejar que el commit final de `get_db`
        # lo dispare) para poder atrapar el IntegrityError acá y traducirlo a un
        # error de dominio prolijo, en vez de un 500 crudo. La única FK sin
        # `ondelete` que apunta a `prestadores.id` es `liquidaciones.prestador_id`
        # (a propósito, ver el modelo) — spsts/tarifarios/tabla_kms cascadean solo,
        # así que cualquier IntegrityError acá es ese caso.
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise PrestadorConLiquidacionesError(prestador_id) from exc
        return True


def _to_entity(row: LiquidacionPrestadorModel) -> Prestador:
    return Prestador(
        id=row.id,
        nombre=row.nombre,
        nombre_corto=row.nombre_corto,
        cuit=row.cuit,
        region=row.region,
        activo=row.activo,
        created_at=row.created_at,
        updated_at=row.updated_at,
        siges_empresa_id=row.siges_empresa_id,
        cd_prestador_id=row.cd_prestador_id,
        siges_base_sucursal_id=row.siges_base_sucursal_id,
    )
